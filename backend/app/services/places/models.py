"""A place in Poland a search is centred on: any city, town or village."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

#: What a search may add around its place. Otodom takes any radius, OLX its own steps.
RADIUS_CHOICES: tuple[int, ...] = (0, 5, 10, 15, 25, 50)

#: Poland, generously: a point outside is a mistake, not a place we can search.
_LAT, _LON = (48.9, 55.0), (14.0, 24.3)


def slugify(text: str) -> str:
    """Bielsko-Biała → bielsko-biala: the way the portals spell places in URLs."""
    text = text.lower().replace("ł", "l")
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "-".join(part for part in "".join(c if c.isalnum() else " " for c in ascii_text).split())


@dataclass(frozen=True)
class Place:
    name: str         # "Zabierzów", as people write it
    path: str         # "malopolskie/krakowski/zabierzow/zabierzow": voivodeship/county/municipality/locality
    region_name: str  # "małopolskie", as the bailiff auctions spell it
    lat: float
    lon: float
    #: "gmina Zabierzów, powiat krakowski, małopolskie" — tells same-named villages apart. Not stored.
    detail: str = ""

    @property
    def slug(self) -> str:
        """The locality alone — how OLX and Morizon name it in their URLs."""
        return self.path.rsplit("/", 1)[-1]

    @property
    def region_slug(self) -> str:
        return self.path.split("/", 1)[0]

    def is_valid(self) -> bool:
        parts = self.path.split("/")
        return (
            bool(self.name.strip()) and len(parts) == 4 and all(parts)
            and _LAT[0] <= self.lat <= _LAT[1] and _LON[0] <= self.lon <= _LON[1]
        )

    @classmethod
    def from_admin(cls, name: str, locality: str, municipality: str, county: str, region: str, lat: float, lon: float) -> Place:
        """Build from administrative names; a city with county rights is its own county and municipality."""
        detail = ", ".join(part for part in (municipality, county, region) if part)
        region = region.removeprefix("województwo ").strip()
        county = county.removeprefix("powiat ").strip() or locality
        municipality = municipality.removeprefix("gmina ").strip() or locality
        path = "/".join(slugify(part) for part in (region, county, municipality, locality))
        return cls(name=name, path=path, region_name=region, lat=lat, lon=lon, detail=detail)
