from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import DatabaseRouter, get_cloud_session, get_private_session
from app.models import Member, Participation
from app.schemas import (
    DeploymentInfo,
    FederatedMember,
    FederatedOverview,
    MemberCreate,
    MemberRead,
    ParticipationCreate,
    ParticipationRead,
    Token,
)
from app.security import constant_time_equal, create_access_token, current_user
from app.services import federated_member, federated_overview


def _seed(router: DatabaseRouter) -> None:
    with router.private_session() as private_db, router.cloud_session() as cloud_db:
        if private_db.scalar(select(Member.id).limit(1)) is not None:
            return
        member = Member(
            full_name="Camille Martin",
            email="camille.martin@example.org",
            postal_code="69003",
            consent=True,
        )
        private_db.add(member)
        private_db.commit()
        cloud_db.add_all(
            [
                Participation(member_ref=member.id, program="Aide alimentaire", hours=3.5),
                Participation(member_ref=member.id, program="Atelier numérique", hours=2.0),
            ]
        )
        cloud_db.commit()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        router = DatabaseRouter(settings)
        application.state.settings = settings
        application.state.databases = router
        if settings.auto_create_schema:
            router.create_schema()
        if settings.seed_demo_data:
            _seed(router)
        yield
        router.dispose()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="API de suivi des adhérents et des activités d'une association.",
        lifespan=lifespan,
    )

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/ready", tags=["system"])
    def ready(request: Request) -> dict[str, str]:
        router: DatabaseRouter = request.app.state.databases
        try:
            with router.private_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            with router.cloud_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Une base est indisponible") from exc
        return {"private": "ready", "cloud": "ready"}

    @application.post(f"{settings.api_prefix}/auth/token", response_model=Token, tags=["auth"])
    def login(form: OAuth2PasswordRequestForm = Depends()) -> Token:
        valid_user = constant_time_equal(form.username, settings.admin_username)
        valid_password = constant_time_equal(
            form.password, settings.admin_password.get_secret_value()
        )
        if not (valid_user and valid_password):
            raise HTTPException(status_code=401, detail="Identifiants invalides")
        return Token(access_token=create_access_token(form.username, settings))

    auth = Depends(current_user)

    @application.get(f"{settings.api_prefix}/routing-policy", tags=["governance"])
    def routing_policy(_: str = auth) -> dict[str, object]:
        return {
            "private": ["full_name", "email", "postal_code", "consent"],
            "cloud": ["member_ref", "program", "hours", "recorded_at"],
            "federation": "application-layer",
            "cross_database_foreign_keys": False,
        }

    @application.get(
        f"{settings.api_prefix}/deployment-info",
        response_model=DeploymentInfo,
        tags=["system"],
    )
    def deployment_info(_: str = auth) -> DeploymentInfo:
        ssl_modes = ("require", "verify-ca", "verify-full")
        cloud_tls = any(
            f"sslmode={mode}" in settings.cloud_database_url for mode in ssl_modes
        )
        return DeploymentInfo(
            mode=settings.deployment_mode,
            private_database="local",
            cloud_database="remote" if settings.deployment_mode == "hybrid" else "local",
            cloud_tls=cloud_tls,
        )

    @application.post(
        f"{settings.api_prefix}/members",
        response_model=MemberRead,
        status_code=status.HTTP_201_CREATED,
        tags=["private"],
    )
    def create_member(
        payload: MemberCreate,
        _: str = auth,
        private_db: Session = Depends(get_private_session),
    ) -> Member:
        member = Member(**payload.model_dump())
        private_db.add(member)
        try:
            private_db.commit()
        except IntegrityError as exc:
            private_db.rollback()
            raise HTTPException(status_code=409, detail="Cet e-mail existe déjà") from exc
        private_db.refresh(member)
        return member

    @application.get(
        f"{settings.api_prefix}/members", response_model=list[MemberRead], tags=["private"]
    )
    def list_members(
        _: str = auth,
        private_db: Session = Depends(get_private_session),
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> list[Member]:
        statement = select(Member).order_by(Member.created_at).offset(offset).limit(limit)
        return list(private_db.scalars(statement))

    @application.post(
        f"{settings.api_prefix}/participations",
        response_model=ParticipationRead,
        status_code=status.HTTP_201_CREATED,
        tags=["cloud"],
    )
    def create_participation(
        payload: ParticipationCreate,
        _: str = auth,
        private_db: Session = Depends(get_private_session),
        cloud_db: Session = Depends(get_cloud_session),
    ) -> Participation:
        if private_db.get(Member, payload.member_ref) is None:
            raise HTTPException(status_code=404, detail="Adhérent inconnu")
        participation = Participation(**payload.model_dump())
        cloud_db.add(participation)
        cloud_db.commit()
        cloud_db.refresh(participation)
        return participation

    @application.get(
        f"{settings.api_prefix}/federated/members/{{member_id}}",
        response_model=FederatedMember,
        tags=["federated"],
    )
    def get_federated_member(
        member_id: UUID,
        _: str = auth,
        private_db: Session = Depends(get_private_session),
        cloud_db: Session = Depends(get_cloud_session),
    ) -> FederatedMember:
        result = federated_member(member_id, private_db, cloud_db)
        if result is None:
            raise HTTPException(status_code=404, detail="Adhérent inconnu")
        return result

    @application.get(
        f"{settings.api_prefix}/federated/overview",
        response_model=FederatedOverview,
        tags=["federated"],
    )
    def get_federated_overview(
        _: str = auth,
        private_db: Session = Depends(get_private_session),
        cloud_db: Session = Depends(get_cloud_session),
    ) -> FederatedOverview:
        return federated_overview(private_db, cloud_db)

    return application


app = create_app()
