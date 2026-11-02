"""Polish cities and how each portal spells them.

A wrong slug returns an empty page rather than an error, so every city
added here should be checked against all four portals.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...core.errors import Invalid


@dataclass(frozen=True)
class City:
    key: str          # ascii slug used in Otodom / OLX / Morizon paths
    label: str        # display name; komornik's `city` parameter
    region_slug: str  # ascii voivodeship slug for Otodom
    region_name: str  # Polish voivodeship name for komornik


CITIES: tuple[City, ...] = (
    City("krakow", "Kraków", "malopolskie", "małopolskie"),
    City("katowice", "Katowice", "slaskie", "śląskie"),
    City("warszawa", "Warszawa", "mazowieckie", "mazowieckie"),
    City("wroclaw", "Wrocław", "dolnoslaskie", "dolnośląskie"),
    City("poznan", "Poznań", "wielkopolskie", "wielkopolskie"),
    City("gdansk", "Gdańsk", "pomorskie", "pomorskie"),
    City("gdynia", "Gdynia", "pomorskie", "pomorskie"),
    City("lodz", "Łódź", "lodzkie", "łódzkie"),
    City("szczecin", "Szczecin", "zachodniopomorskie", "zachodniopomorskie"),
    City("lublin", "Lublin", "lubelskie", "lubelskie"),
    City("bydgoszcz", "Bydgoszcz", "kujawsko-pomorskie", "kujawsko-pomorskie"),
    City("rzeszow", "Rzeszów", "podkarpackie", "podkarpackie"),
)

_BY_KEY = {city.key: city for city in CITIES}


def get_city(key: str) -> City:
    city = _BY_KEY.get((key or "").strip().lower())
    if city is None:
        raise Invalid("city.unsupported", key=key, choices=", ".join(_BY_KEY))
    return city


def city_names() -> frozenset[str]:
    """Every spelling of every city — noise for cross-portal matching."""
    return frozenset(name.lower() for city in CITIES for name in (city.key, city.label))
