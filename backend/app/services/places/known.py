"""Places we know without asking anyone: the big cities (also the older ``city`` keys of saved
searches) and a few villages, so local runs and tests need no network."""

from __future__ import annotations

from .models import Place

KNOWN_PLACES: tuple[Place, ...] = (
    Place("Kraków", "malopolskie/krakow/krakow/krakow", "małopolskie", 50.0614, 19.9366),
    Place("Katowice", "slaskie/katowice/katowice/katowice", "śląskie", 50.2649, 19.0238),
    Place("Warszawa", "mazowieckie/warszawa/warszawa/warszawa", "mazowieckie", 52.2297, 21.0122),
    Place("Wrocław", "dolnoslaskie/wroclaw/wroclaw/wroclaw", "dolnośląskie", 51.1079, 17.0385),
    Place("Poznań", "wielkopolskie/poznan/poznan/poznan", "wielkopolskie", 52.4064, 16.9252),
    Place("Gdańsk", "pomorskie/gdansk/gdansk/gdansk", "pomorskie", 54.3520, 18.6466),
    Place("Gdynia", "pomorskie/gdynia/gdynia/gdynia", "pomorskie", 54.5189, 18.5305),
    Place("Łódź", "lodzkie/lodz/lodz/lodz", "łódzkie", 51.7592, 19.4560),
    Place("Szczecin", "zachodniopomorskie/szczecin/szczecin/szczecin", "zachodniopomorskie", 53.4285, 14.5528),
    Place("Lublin", "lubelskie/lublin/lublin/lublin", "lubelskie", 51.2465, 22.5684),
    Place("Bydgoszcz", "kujawsko-pomorskie/bydgoszcz/bydgoszcz/bydgoszcz", "kujawsko-pomorskie", 53.1235, 18.0084),
    Place("Rzeszów", "podkarpackie/rzeszow/rzeszow/rzeszow", "podkarpackie", 50.0412, 21.9991),
    Place("Wieliczka", "malopolskie/wielicki/wieliczka/wieliczka", "małopolskie", 49.9871, 20.0647),
    Place("Zabierzów", "malopolskie/krakowski/zabierzow/zabierzow", "małopolskie", 50.1146, 19.7993),
    Place("Bibice", "malopolskie/krakowski/zielonki/bibice", "małopolskie", 50.1240, 19.9552),
)

_BY_SLUG = {place.slug: place for place in KNOWN_PLACES}


def known_place(slug: str) -> Place | None:
    """The place for an old ``city`` key such as "krakow"."""
    return _BY_SLUG.get((slug or "").strip().lower())


def place_names() -> frozenset[str]:
    """Every spelling of every known place — noise for cross-portal matching."""
    return frozenset(name.lower() for place in KNOWN_PLACES for name in (place.slug, place.name))
