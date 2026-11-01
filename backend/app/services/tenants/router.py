from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends

from ...core.container import Container
from ..auth.dependencies import current_user, get_container
from ..users.models import User
from .schemas import CredentialsOut, CredentialsRequest, DatabaseInfoOut

router = APIRouter(prefix="/api/database", tags=["database"])


@router.get("", response_model=DatabaseInfoOut)
def info(user: User = Depends(current_user), container: Container = Depends(get_container)) -> DatabaseInfoOut:
    tenant = container.tenants.get(user.id)
    return DatabaseInfoOut(
        provider=tenant.provider,
        db_name=tenant.db_name,
        created_at=tenant.created_at,
        credentials_available=container.users.plan_of(user).database_credentials,
    )


@router.post("/credentials", response_model=CredentialsOut)
def credentials(
    body: CredentialsRequest,
    user: User = Depends(current_user),
    container: Container = Depends(get_container),
) -> CredentialsOut:
    return CredentialsOut(**asdict(container.tenants.credentials(user, read_only=body.read_only)))
