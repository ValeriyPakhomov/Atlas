"""Alembic environment for Atlas PostgreSQL migrations."""

from __future__ import annotations

import os
from logging.config import fileConfig
from typing import Any

from alembic import context
from sqlalchemy import CheckConstraint, engine_from_config, pool

from atlas.persistence.database import normalize_postgresql_url
from atlas.persistence.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = (
    os.getenv("ATLAS_DATABASE_DIRECT_URL")
    or os.getenv("ATLAS_DATABASE_URL")
    or config.get_main_option("sqlalchemy.url")
)
config.set_main_option("sqlalchemy.url", normalize_postgresql_url(database_url))

target_metadata = Base.metadata
metadata_check_constraint_names = frozenset(
    constraint.name
    for table in target_metadata.tables.values()
    for constraint in table.constraints
    if isinstance(constraint, CheckConstraint) and constraint.name is not None
)


def include_object(
    _object: Any,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to: Any,
) -> bool:
    """Pair reflected named checks that Alembic cannot normalize reliably.

    SQLAlchemy's portable non-native Enum checks reflect as textual constraints. The
    Alembic PostgreSQL comparator cannot associate them with their metadata counterparts,
    even when their stable names match, and otherwise reports false removals.
    """

    return not (
        type_ == "check_constraint"
        and reflected
        and compare_to is None
        and name in metadata_check_constraint_names
    )


def run_migrations_offline() -> None:
    """Run migrations without creating an Engine."""

    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against PostgreSQL."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
