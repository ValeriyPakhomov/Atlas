"""Shared test fixtures and repository paths."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DOMAIN_ROOT = REPO_ROOT / "packages" / "atlas" / "domain"
PACKAGES_ROOT = REPO_ROOT / "packages" / "atlas"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT
