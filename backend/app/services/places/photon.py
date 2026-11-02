"""Photon (OpenStreetMap, by Komoot) finds the place; Poland's geoportal (ULDK, GUGiK) says which
municipality it is in — the part of the path Otodom needs and Photon does not give."""

from __future__ import annotations

import re

from .http import PoliteClient
from .models import Place

_POLAND = "14.0,48.9,24.3,55.0"
_SETTLEMENTS = [("osm_tag", f"place:{kind}") for kind in ("city", "town", "village", "hamlet")]


class PhotonDirectory:
    def __init__(self, photon: PoliteClient | None = None, uldk: PoliteClient | None = None):
        self._photon = photon or PoliteClient("https://photon.komoot.io", min_gap_seconds=0.2)
        self._uldk = uldk or PoliteClient("https://uldk.gugik.gov.pl", min_gap_seconds=0.1)

    def search(self, text: str) -> list[Place] | None:
        params = [("q", text.strip()), ("limit", "8"), ("bbox", _POLAND), *_SETTLEMENTS]
        answer = self._photon.json("/api/", params)
        if answer is None:
            return None
        places = [place for feature in answer.get("features", []) if (place := self._place(feature))]
        return list({place.path: place for place in places}.values())[:5]

    def at(self, lat: float, lon: float) -> Place | None:
        answer = self._photon.json("/reverse", {"lat": f"{lat:.5f}", "lon": f"{lon:.5f}", "limit": 1})
        features = (answer or {}).get("features") or []
        return self._place(features[0]) if features else None

    def _place(self, feature: dict) -> Place | None:
        props = feature.get("properties") or {}
        if props.get("countrycode") not in (None, "PL"):
            return None
        lon, lat = feature.get("geometry", {}).get("coordinates", (None, None))
        name = props.get("name") if props.get("osm_value") in ("city", "town", "village", "hamlet") else props.get("city")
        commune = self._commune(lat, lon) if lat is not None else None
        if not name or commune is None:
            return None
        municipality, county, region = commune
        place = Place.from_admin(name=name, locality=name, municipality=municipality, county=county, region=region, lat=lat, lon=lon)
        return place if place.is_valid() else None

    def _commune(self, lat: float, lon: float) -> tuple[str, str, str] | None:
        """("gmina Zielonki", "powiat krakowski", "małopolskie") for a point, from ULDK."""
        params = {"request": "GetCommuneByXY", "xy": f"{lon:.6f},{lat:.6f},4326", "result": "commune,county,voivodeship"}
        answer = self._uldk.text("/", params)
        lines = (answer or "").strip().splitlines()
        if len(lines) < 2 or lines[0].strip() != "0":
            return None
        parts = lines[1].split("|")
        if len(parts) != 3:
            return None
        commune, county, region = parts
        # "Kraków (miasto)" is a city with county rights; the bracket is not part of the name.
        commune = re.sub(r"\s*\(.*?\)\s*$", "", commune).strip()
        return f"gmina {commune}", county, region
