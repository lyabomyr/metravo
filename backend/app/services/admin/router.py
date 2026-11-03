from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...core.container import Container
from ..auth.dependencies import admin_user, get_container
from ..auth.schemas import UserOut
from ..monitoring.schemas import SystemOut
from ..users.models import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/system", response_model=SystemOut)
def system(_: User = Depends(admin_user), container: Container = Depends(get_container)) -> SystemOut:
    """Memory, CPU, the last scan, active alerts and recent warnings of this instance."""
    container.monitor.check()
    return SystemOut.of(container.monitor.status, container.recent_logs.entries())


@router.get("/database")
def database(_: User = Depends(admin_user), container: Container = Depends(get_container)) -> list[dict]:
    """Every table with its rows and size, the biggest first."""
    return [asdict(table) for table in container.database_usage.tables()]


class PlanChange(BaseModel):
    plan: str


@router.get("/overview")
def overview(_: User = Depends(admin_user), container: Container = Depends(get_container)) -> dict:
    return asdict(container.admin.overview())


@router.get("/users", response_model=list[UserOut])
def users(_: User = Depends(admin_user), container: Container = Depends(get_container)):
    return [UserOut.of(user) for user in container.admin.users()]


@router.put("/users/{user_id}/plan", response_model=UserOut)
def set_plan(user_id: str, body: PlanChange, _: User = Depends(admin_user), container: Container = Depends(get_container)):
    return UserOut.of(container.admin.set_plan(user_id, body.plan))
