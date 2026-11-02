"""Finding places by name or by a point on the map."""

from __future__ import annotations

import math
from typing import Protocol

from ...core.errors import Unavailable
from .known import KNOWN_PLACES
from .models import Place, slugify


class PlaceSource(Protocol):
    """One service. ``None`` means it failed (not "nothing found"), so the next one is asked."""

    def search(self, text: str) -> list[Place] | None: ...

    def at(self, lat: float, lon: float) -> Place | None: ...


class KnownPlaceDirectory:
    """The built-in list — local runs and tests, and the big cities when every service is down."""

    def search(self, text: str) -> list[Place]:
        wanted = slugify(text)
        return [place for place in KNOWN_PLACES if wanted and slugify(place.name).startswith(wanted)][:5]

    def at(self, lat: float, lon: float) -> Place | None:
        nearest = min(KNOWN_PLACES, key=lambda place: _km(lat, lon, place.lat, place.lon))
        return nearest if _km(lat, lon, nearest.lat, nearest.lon) <= 30 else None


class PlaceDirectory:
    """Asks each service in turn; the built-in cities are always among the answers."""

    def __init__(self, sources: list[PlaceSource]):
        self._sources = sources
        self._known = KnownPlaceDirectory()

    def search(self, text: str) -> list[Place]:
        known = self._known.search(text)
        for source in self._sources:
            found = source.search(text)
            if found is not None:
                return _unique(known + found)[:5]
        if known or not self._sources:  # offline (local runs, tests): the built-in list is the whole answer
            return known
        raise Unavailable("places.unavailable")

    def at(self, lat: float, lon: float) -> Place | None:
        for source in self._sources:
            if (place := source.at(lat, lon)) is not None:
                return place
        return self._known.at(lat, lon)


def _unique(places: list[Place]) -> list[Place]:
    return list({place.path: place for place in places}.values())


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))
