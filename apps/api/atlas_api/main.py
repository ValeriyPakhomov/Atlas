"""Atlas API application factory."""

from __future__ import annotations

from fastapi import FastAPI

from atlas import __version__
from atlas.config import get_settings

from .routes import health


def create_app() -> FastAPI:
    """Build the Atlas FastAPI application.

    Queue 00 exposes health only. Read endpoints from blueprint §23 are added by the
    queue items that make their underlying state real; an endpoint that returns a
    plausible empty shape before its engine exists would violate A06.
    """
    settings = get_settings()
    app = FastAPI(
        title="Atlas",
        version=__version__,
        summary="Read-only personal intelligence system.",
        docs_url="/docs" if settings.environment in {"local", "ci"} else None,
        redoc_url=None,
    )
    app.include_router(health.router)
    return app


app = create_app()
