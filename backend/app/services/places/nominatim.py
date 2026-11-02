"""OpenStreetMap's own geocoder. Exact municipalities, but it blocks many shared cloud addresses."""

from __future__ import annotations

from .http import PoliteClient
from .models import Place

#: Search results are places people live in, not streets or shops.
_SETTLEMENTS = ("city", "town", "village", "hamlet", "suburb", "quarter")


class NominatimDirectory:
    def __init__(self, client: PoliteClient | None = None):
        # Nominatim's policy: an identifying User-Agent and at most one request a second.
        self._client = client or PoliteClient("https://nominatim.openstreetmap.org", min_gap_seconds=1.0)

    def search(self, text: str) -> list[Place] | None:
        rows = self._client.json("/search", {"q": text.strip(), "countrycodes": "pl", "format": "jsonv2", "addressdetails": 1, "limit": 10})
        if rows is None:
            return None
        places = [place for row in rows if row.get("addresstype") in _SETTLEMENTS and (place := _place(row))]
        return list({place.path: place for place in places}.values())[:5]

    def at(self, lat: float, lon: float) -> Place | None:
        row = self._client.json("/reverse", {"lat": f"{lat:.5f}", "lon": f"{lon:.5f}", "format": "jsonv2", "addressdetails": 1, "zoom": 14})
        return _place(row, lat, lon) if isinstance(row, dict) and "address" in row else None


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
