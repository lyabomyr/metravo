from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, BackgroundTasks, Depends, Header

from ...core.container import Container
from ...core.errors import Forbidden
from ..auth.dependencies import admin_user, current_user, get_container
from ..users.models import User

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("/mine")
def scan_mine(user: User = Depends(current_user), container: Container = Depends(get_container)) -> dict:
    """Scan the caller's due searches now. The plan interval still applies."""
    return asdict(container.scanner.check_now(user))


@router.post("/all")
def scan_all(_: User = Depends(admin_user), container: Container = Depends(get_container)) -> dict:
    return asdict(container.scanner.run())


@router.post("/cron", status_code=202)
def scan_from_cron(
    background: BackgroundTasks,
    x_cron_secret: str = Header(default=""),
    container: Container = Depends(get_container),
) -> dict:
    """Entry point for an external scheduler (cron-job.org). Returns at once."""
    if not container.settings.cron_secret or x_cron_secret != container.settings.cron_secret:
        raise Forbidden("Bad cron secret")
    background.add_task(container.scanner.run)
    return {"accepted": True}
