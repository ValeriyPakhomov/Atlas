"""Liveness and data-freshness endpoints.

``/health`` answers "is the process up". ``/health/data`` answers the far more
important Atlas question (A06, blueprint §28): "is the state Atlas would serve
actually fresh, or is it silently stale". Queue 02+ populates the source list;
until then the endpoint reports an explicitly unknown freshness rather than
implying that everything is fine.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from atlas import __version__
from atlas.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    environment: str
    execution_enabled: Literal[False]


class DataHealthResponse(BaseModel):
    status: Literal["unknown"]
    reason: str
    stale_sources: list[str]
    checked_sources: int


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings: Settings = get_settings()
    return HealthResponse(
        status="ok",
        version=__version__,
        environment=settings.environment,
        execution_enabled=settings.execution_enabled,
    )


@router.get("/health/data", response_model=DataHealthResponse)
def data_health() -> DataHealthResponse:
    return DataHealthResponse(
        status="unknown",
        reason="no source registry yet; source freshness lands in Queue 02",
        stale_sources=[],
        checked_sources=0,
    )
