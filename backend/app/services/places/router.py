from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...core.container import Container
from ..auth.dependencies import current_user, get_container
from ..searches.schemas import PlaceIO
from ..users.models import User

router = APIRouter(prefix="/api/places", tags=["places"])


@router.get("", response_model=list[PlaceIO])
def search_places(
    q: str = Query(min_length=2, max_length=80),
    _: User = Depends(current_user),
    container: Container = Depends(get_container),
):
    """Cities, towns and villages in Poland by name. Signed-in only: each lookup is a request to OpenStreetMap."""
    return [PlaceIO.of(place) for place in container.places.search(q)]


@router.get("/at", response_model=PlaceIO | None)
def place_at(
    lat: float = Query(ge=48.9, le=55.0),
    lon: float = Query(ge=14.0, le=24.3),
    _: User = Depends(current_user),
    container: Container = Depends(get_container),
):
    """The place at a point the user clicked on the map."""
    place = container.places.at(lat, lon)
    return PlaceIO.of(place) if place else None
