"""Configuration must survive hosting platforms and fail safe when unset.

Two defects motivated these tests, both reproduced against the deployed API:

1. A platform that materialises a declared-but-unset variable as an empty string
   (`ATLAS_ENVIRONMENT=`) crashed the process at import: the empty string overrode
   the default and failed `Literal` validation.
2. With the variable *absent* the environment resolved to ``local``, which opened
   the interactive API docs — in production. The crash in (1) was masking (2).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from atlas.config import Settings, get_settings
from atlas_api.main import create_app

ATLAS_VARS = (
    "ATLAS_ENVIRONMENT",
    "ATLAS_OWNER_TIMEZONE",
    "ATLAS_BASE_CURRENCY",
    "ATLAS_DATABASE_URL",
    "ATLAS_DATABASE_DIRECT_URL",
)


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """No ATLAS_* variables, no ``.env`` within reach, and no cached settings.

    ``get_settings`` is deliberately cached for the process lifetime, so the cache
    has to be cleared around any test that varies the environment — otherwise the
    first test to run fixes the configuration for every test after it.
    """
    for name in ATLAS_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.parametrize("name", ATLAS_VARS)
def test_blank_variable_is_treated_as_unset(
    name: str, clean_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A blank value is the absence of a value, and must not override a default."""
    monkeypatch.setenv(name, "")
    settings = Settings()  # must not raise
    assert settings.environment == "production"
    assert settings.base_currency == "USD"
    assert settings.owner_timezone == "Europe/Istanbul"


def test_unset_environment_defaults_to_the_most_restrictive(clean_env: None) -> None:
    """Missing configuration must never resolve to the most permissive setting."""
    assert Settings().environment == "production"


def test_docs_are_closed_when_environment_is_unconfigured(clean_env: None) -> None:
    """The defect this guards: unconfigured deployment serving public API docs."""
    assert create_app().docs_url is None


@pytest.mark.parametrize("environment", ["local", "ci"])
def test_docs_are_open_only_in_developer_environments(
    environment: str, clean_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_ENVIRONMENT", environment)
    assert create_app().docs_url == "/docs"


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_docs_are_closed_in_deployed_environments(
    environment: str, clean_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ATLAS_ENVIRONMENT", environment)
    assert create_app().docs_url is None


def test_an_invalid_environment_still_fails_loudly(
    clean_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ignoring blanks must not weaken validation of values that are actually set."""
    monkeypatch.setenv("ATLAS_ENVIRONMENT", "prod")
    with pytest.raises(ValidationError):
        Settings()


def test_health_reports_the_configured_environment(
    clean_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A misconfiguration must be visible rather than silent (A06)."""
    from fastapi.testclient import TestClient

    monkeypatch.setenv("ATLAS_ENVIRONMENT", "staging")
    with TestClient(create_app()) as client:
        body = client.get("/health").json()
    assert body["environment"] == "staging"
    assert body["execution_enabled"] is False
