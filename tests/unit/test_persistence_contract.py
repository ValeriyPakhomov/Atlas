"""Mechanical Queue 01 persistence-boundary checks."""

from __future__ import annotations

import pytest

from atlas.persistence.database import create_engine_from_url, normalize_postgresql_url
from atlas.persistence.models import Base


def test_every_persisted_column_declares_schema_tiers() -> None:
    missing: list[str] = []
    for table in Base.metadata.sorted_tables:
        for column in table.columns:
            if "schema_max_tier" not in column.info or "schema_default_tier" not in column.info:
                missing.append(f"{table.name}.{column.name}")
    assert missing == []


def test_sqlite_fallback_is_rejected() -> None:
    with pytest.raises(ValueError, match="PostgreSQL"):
        create_engine_from_url("sqlite+pysqlite:///:memory:")


def test_generic_provider_url_selects_psycopg_3() -> None:
    assert normalize_postgresql_url("postgresql://atlas@host/database") == (
        "postgresql+psycopg://atlas@host/database"
    )
