"""ADR-0003: Atlas V1 has no configuration path to external execution."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from atlas.config import Settings


def test_execution_is_disabled_by_default() -> None:
    assert Settings().execution_enabled is False


def test_execution_cannot_be_enabled_by_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_EXECUTION_ENABLED", "true")
    with pytest.raises(ValidationError):
        Settings()


def test_settings_are_immutable() -> None:
    settings = Settings()
    with pytest.raises(ValidationError):
        settings.environment = "production"


def test_base_currency_must_be_iso4217(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ATLAS_BASE_CURRENCY", "dollars")
    with pytest.raises(ValidationError):
        Settings()
    monkeypatch.setenv("ATLAS_BASE_CURRENCY", "eur")
    assert Settings().base_currency == "EUR"
