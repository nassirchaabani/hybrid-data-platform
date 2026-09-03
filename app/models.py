from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Float, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class PrivateBase(DeclarativeBase):
    pass


class CloudBase(DeclarativeBase):
    pass


class Member(PrivateBase):
    """Informations permettant d'identifier un adhérent, conservées côté privé."""

    __tablename__ = "members"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    postal_code: Mapped[str] = mapped_column(String(20))
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class Participation(CloudBase):
    """Participation pseudonymisée, sans clé étrangère vers la base privée."""

    __tablename__ = "participations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    member_ref: Mapped[UUID] = mapped_column(Uuid, index=True)
    program: Mapped[str] = mapped_column(String(120), index=True)
    hours: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
