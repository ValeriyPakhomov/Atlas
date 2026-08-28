"""Queue 00 acceptance: the empty application boots and answers health."""

from __future__ import annotations

from fastapi.testclient import TestClient

from atlas_api.main import create_app


def test_app_boots_and_reports_health() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["execution_enabled"] is False


def test_data_health_reports_unknown_rather_than_ok() -> None:
    """A06: absent freshness data must never be presented as healthy."""
    with TestClient(create_app()) as client:
        response = client.get("/health/data")
    assert response.status_code == 200
    assert response.json()["status"] == "unknown"


def test_no_feature_endpoints_exist_yet() -> None:
    """Queue 00 must not ship §23 read endpoints backed by nothing."""
    paths = set(create_app().openapi()["paths"])
    assert paths == {"/health", "/health/data"}
    assert not {p for p in paths if p.startswith(("/world", "/personal", "/impacts"))}
