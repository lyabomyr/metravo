from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from ...core.container import Container
from ..auth.dependencies import current_user, get_container
from ..users.models import User
from .schemas import ListingOut, PriceChangeOut

router = APIRouter(prefix="/api/listings", tags=["listings"])


@router.get("", response_model=list[ListingOut])
def latest(
    search_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(current_user),
    container: Container = Depends(get_container),
):
    return [ListingOut(**asdict(item)) for item in container.listings.latest(user, search_id, limit)]


@router.get("/price-changes", response_model=list[PriceChangeOut])
def price_changes(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(current_user),
    container: Container = Depends(get_container),
):
    return [PriceChangeOut(**asdict(item)) for item in container.listings.price_changes(user, limit)]
