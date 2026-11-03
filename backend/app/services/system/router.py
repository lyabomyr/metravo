"""Health check and the public configuration the frontend boots with."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core.config import parse_web_config
from ...core.container import Container
from ..auth.dependencies import get_container
from ..places.models import RADIUS_CHOICES
from ..scanning.service import FIRST_DELIVERY
from ..searches.models import DEFAULT_REJECT_KEYWORDS, SCAN_INTERVALS

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
        "firebase": parse_web_config(settings.firebase_web_config),
        "telegram_bot": settings.telegram_bot_username,
        "billing_provider": settings.billing_provider,
        "sources": container.connectors.names,
        "source_capabilities": container.connectors.capabilities(),
        "scan_intervals": list(SCAN_INTERVALS),
        "plan_min_intervals": {plan.code: plan.min_interval_minutes for plan in container.plans},
        "plan_sources": {plan.code: list(plan.sources) for plan in container.plans},
        "radius_choices": list(RADIUS_CHOICES),
        "default_reject_keywords": list(DEFAULT_REJECT_KEYWORDS),
        "first_batch": FIRST_DELIVERY,
        # "off", "waiting", "ok" or "error" — whether OLX and Otodom alert emails are being read.
        "mail_alerts": container.mail_alerts.public_state,
        "portal_status": container.portal_access.status(),
    }
