"""Real PostgreSQL fixtures for Queue 01."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session


@pytest.fixture(scope="session")
def postgres_url() -> str:
    url = os.environ.get("ATLAS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("ATLAS_TEST_DATABASE_URL is required for PostgreSQL integration tests")
    if not url.startswith(("postgresql://", "postgresql+psycopg://")):
        pytest.fail("integration tests require PostgreSQL; SQLite is not supported")
    return url


@pytest.fixture(scope="session")
def migrated_engine(postgres_url: str) -> Iterator[Engine]:
    root = Path(__file__).parents[2]
    config = Config(root / "alembic.ini")
    config.set_main_option("sqlalchemy.url", postgres_url)

    # Prove both bootstrap from zero and the supported downgrade/upgrade path.
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    engine = create_engine(postgres_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def db_session(migrated_engine: Engine) -> Iterator[Session]:
    connection = migrated_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
