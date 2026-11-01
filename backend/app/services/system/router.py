"""Health check and the public configuration the frontend boots with."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends

from ...core.container import Container
from ..auth.dependencies import get_container
from ..connectors.cities import CITIES

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/config")
def public_config(container: Container = Depends(get_container)) -> dict:
    """Everything here is safe to publish — it is shipped to every browser."""
    settings = container.settings
    return {
        "env": settings.env,
        "auth_providers": container.auth.provider_names,
        "firebase": json.loads(settings.firebase_web_config) if settings.firebase_web_config else None,
        "telegram_bot": settings.telegram_bot_username,
        "billing_provider": settings.billing_provider,
        "sources": container.connectors.names,
        "source_capabilities": container.connectors.capabilities(),
        "cities": [{"key": city.key, "label": city.label} for city in CITIES],
    }
