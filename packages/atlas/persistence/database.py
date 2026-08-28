"""Database engine and session construction."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def normalize_postgresql_url(database_url: str) -> str:
    """Select psycopg 3 when a provider supplies a generic PostgreSQL URL."""

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql+psycopg://"):
        return database_url
    raise ValueError("Atlas persistence requires PostgreSQL; SQLite is not supported")


def create_engine_from_url(database_url: str, *, echo: bool = False) -> Engine:
    """Create a PostgreSQL engine without leaking it into the domain package."""

    return create_engine(normalize_postgresql_url(database_url), echo=echo, pool_pre_ping=True)


def session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return the Queue 01 synchronous unit-of-work factory."""

    return sessionmaker(bind=engine, expire_on_commit=False)
