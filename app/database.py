from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.models import CloudBase, PrivateBase


def _engine(url: str) -> Engine:
    options: dict[str, object] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **options)


class DatabaseRouter:
    """Regroupe les deux connexions sans mélanger leurs modèles."""

    def __init__(self, settings: Settings) -> None:
        self.private_engine = _engine(settings.private_database_url)
        self.cloud_engine = _engine(settings.cloud_database_url)
        self.private_session = sessionmaker(self.private_engine, expire_on_commit=False)
        self.cloud_session = sessionmaker(self.cloud_engine, expire_on_commit=False)

    def create_schema(self) -> None:
        PrivateBase.metadata.create_all(self.private_engine)
        CloudBase.metadata.create_all(self.cloud_engine)

    def dispose(self) -> None:
        self.private_engine.dispose()
        self.cloud_engine.dispose()


def get_private_session(request: Request) -> Generator[Session, None, None]:
    with request.app.state.databases.private_session() as session:
        yield session


def get_cloud_session(request: Request) -> Generator[Session, None, None]:
    with request.app.state.databases.cloud_session() as session:
        yield session
