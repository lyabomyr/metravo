"""Finding places by name or by a point on the map."""

from __future__ import annotations

import logging
import math
import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict

import requests

from .known import KNOWN_PLACES
from .models import Place, slugify

log = logging.getLogger(__name__)

NOMINATIM = "https://nominatim.openstreetmap.org"
#: Nominatim's policy: an identifying User-Agent and at most one request a second.
USER_AGENT = "Metravo/1.0 (flat alerts; https://github.com/lyabomyr/metravo)"
MIN_GAP_SECONDS = 1.0
#: Search results are places people live in, not streets or shops.
_SETTLEMENTS = ("city", "town", "village", "hamlet", "suburb", "quarter")


class PlaceDirectory(ABC):
    @abstractmethod
    def search(self, text: str) -> list[Place]:
        """Places whose name matches, best first."""

    @abstractmethod
    def at(self, lat: float, lon: float) -> Place | None:
        """The place at a point on the map."""


class KnownPlaceDirectory(PlaceDirectory):
    """The built-in list — local runs and tests, no network."""

    def search(self, text: str) -> list[Place]:
        wanted = slugify(text)
        return [place for place in KNOWN_PLACES if wanted and slugify(place.name).startswith(wanted)][:5]

    def at(self, lat: float, lon: float) -> Place | None:
        nearest = min(KNOWN_PLACES, key=lambda place: _km(lat, lon, place.lat, place.lon))
        return nearest if _km(lat, lon, nearest.lat, nearest.lon) <= 30 else None


class NominatimDirectory(PlaceDirectory):
    """OpenStreetMap's geocoder: every city, town and village in Poland, free, one request a second."""

    def __init__(self, session: requests.Session | None = None, cache_size: int = 500):
        self._http = session or requests.Session()
        self._http.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "pl"})
        self._cache: OrderedDict[str, object] = OrderedDict()
        self._cache_size = cache_size
        self._lock = threading.Lock()
        self._last_call = 0.0

    def search(self, text: str) -> list[Place]:
        rows = self._get("/search", {"q": text.strip(), "countrycodes": "pl", "format": "jsonv2", "addressdetails": 1, "limit": 10})
        places = [place for row in rows or [] if row.get("addresstype") in _SETTLEMENTS and (place := _place(row))]
        return list({place.path: place for place in places}.values())[:5]

    def at(self, lat: float, lon: float) -> Place | None:
        row = self._get("/reverse", {"lat": f"{lat:.5f}", "lon": f"{lon:.5f}", "format": "jsonv2", "addressdetails": 1, "zoom": 14})
        return _place(row, lat, lon) if isinstance(row, dict) and "address" in row else None

    def _get(self, path: str, params: dict):
        key = f"{path}?{sorted(params.items())}"
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            time.sleep(max(0.0, self._last_call + MIN_GAP_SECONDS - time.monotonic()))
            self._last_call = time.monotonic()
            try:
                response = self._http.get(NOMINATIM + path, params=params, timeout=10)
                response.raise_for_status()
                result = response.json()
            except (requests.RequestException, ValueError) as error:
                log.warning("place lookup failed: %s", error)
                return None
            self._cache[key] = result
            if len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
            return result


def _place(row: dict, lat: float | None = None, lon: float | None = None) -> Place | None:
    address = row.get("address") or {}
    locality = address.get("city") or address.get("town") or address.get("village") or address.get("hamlet")
    region = address.get("state")
    if not locality or not region:
        return None
    place = Place.from_admin(
        name=locality,
        locality=locality,
        municipality=address.get("municipality", ""),
        county=address.get("county", ""),
        region=region,
        lat=float(row.get("lat", lat)),
        lon=float(row.get("lon", lon)),
    )
    return place if place.is_valid() else None


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))
