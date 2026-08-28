"""Runtime configuration for Atlas services.

Configuration is infrastructure, not domain: ``packages/atlas/domain`` must never
import this module. Values are read once at process start and treated as immutable.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "ci", "staging", "production"]


class Settings(BaseSettings):
    """Process configuration, loaded from environment or ``.env``."""

    model_config = SettingsConfigDict(
        env_prefix="ATLAS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    environment: Environment = "local"
    owner_timezone: str = "Europe/Istanbul"
    base_currency: str = "USD"

    database_url: str = "postgresql+psycopg://atlas:atlas@localhost:5432/atlas"
    database_direct_url: str | None = None
    test_database_url: str = "postgresql+psycopg://atlas:atlas@localhost:5433/atlas_test"

    # ADR-0003: Atlas V1 is read-only with respect to money, brokers, wallets and
    # external systems. There is no configuration path that enables execution; the
    # field exists only so the guarantee is assertable in tests and observable in logs.
    execution_enabled: Literal[False] = Field(default=False, frozen=True)

    @field_validator("base_currency")
    @classmethod
    def _upper_currency(cls, value: str) -> str:
        if len(value) != 3 or not value.isalpha():
            raise ValueError("base_currency must be a 3-letter ISO 4217 code")
        return value.upper()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton."""
    return Settings()
