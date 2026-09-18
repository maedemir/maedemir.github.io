from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from spatial_omics_litdb.config import Settings
from spatial_omics_litdb.models import Base


def _sqlite_connect_args(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def make_engine(settings: Settings):
    engine = create_engine(
        settings.database_url,
        future=True,
        echo=False,
        connect_args=_sqlite_connect_args(settings.database_url),
    )

    if settings.database_url.startswith("sqlite"):

        @event.listens_for(Engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ARG001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine


def init_db(engine) -> None:
    Base.metadata.create_all(engine)


def session_factory(engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db_dep(factory: sessionmaker[Session]):
    def _get_db() -> Generator[Session, None, None]:
        db = factory()
        try:
            yield db
        finally:
            db.close()

    return _get_db
