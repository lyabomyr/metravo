"""Each connector parses its saved fixture page into the expected listings."""

import json

import pytest

from app.services.connectors.fetchers import FixturePageFetcher
from app.services.connectors.komornik.connector import KomornikConnector
from app.services.connectors.models import DealType, Market, PropertyType, SearchQuery
from app.services.connectors.morizon.connector import MorizonConnector
from app.services.connectors.olx.connector import OlxConnector
from app.services.connectors.otodom.connector import OtodomConnector
from app.services.places.known import known_place
from tests.unit.conftest import FIXTURES

KRAKOW = known_place("krakow")
QUERY = SearchQuery(place=KRAKOW, max_price=610000, min_area=39)


def scan(connector_class):
    connector = connector_class(FixturePageFetcher(str(FIXTURES)))
    return connector.scan(connector.build_url(QUERY))


def test_otodom_reads_next_data():
    result = scan(OtodomConnector)
    assert result.ok
    first = result.listings[0]
    assert (first.external_id, first.price, first.area, first.rooms) == ("101", 520000, 45.0, 2)
    assert first.location == "Długa, Stare Miasto, Kraków"
    assert first.url == "https://www.otodom.pl/pl/oferta/dluga-101"
    assert first.image_url == "https://img.example/101.jpg"
    assert len(result.listings) == 4


def test_olx_strips_dates_and_skips_otodom_reposts():
    result = scan(OlxConnector)
    assert [listing.external_id for listing in result.listings] == ["301", "302"]
    assert result.listings[1].location == "Kraków, Bronowice"
    assert result.listings[1].area == 42.0


def test_morizon_ignores_icons_when_picking_a_photo():
    listing = scan(MorizonConnector).listings[0]
    assert (listing.external_id, listing.price, listing.area, listing.rooms) == ("mzn200", 555000, 50.0, 3)
    assert listing.image_url == "https://img.example/mzn200.jpg"


def test_komornik_resolves_devalue_references():
    listing = scan(KomornikConnector).listings[0]
    assert listing.external_id == "9001"
    assert listing.price == 300000
    assert listing.area == 48.5
    assert listing.location == "Dembowskiego, Kraków, małopolskie"


@pytest.mark.parametrize(
    ("connector_class", "deal", "kind", "expected"),
    [
        (OtodomConnector, DealType.SALE, PropertyType.FLAT,
         "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/malopolskie/krakow/krakow/krakow?distanceRadius=0&priceMax=610000&areaMin=39"),
        (OtodomConnector, DealType.RENT, PropertyType.HOUSE, "/pl/wyniki/wynajem/dom/malopolskie/"),
        (OlxConnector, DealType.RENT, PropertyType.FLAT, "/nieruchomosci/mieszkania/wynajem/krakow/"),
        (MorizonConnector, DealType.RENT, PropertyType.FLAT, "morizon.pl/do-wynajecia/mieszkania/najnowsze/krakow/"),
        (MorizonConnector, DealType.SALE, PropertyType.HOUSE, "morizon.pl/domy/najnowsze/krakow/"),
        (KomornikConnector, DealType.SALE, PropertyType.FLAT, "subCategory=APARTMENTS&province=ma%C5%82opolskie&city=Krak%C3%B3w"),
        (KomornikConnector, DealType.SALE, PropertyType.HOUSE, "subCategory=HOUSES"),
    ],
)
def test_urls_are_built_from_the_search(connector_class, deal, kind, expected):
    query = SearchQuery(place=KRAKOW, deal_type=deal, property_type=kind, max_price=610000, min_area=39)
    assert expected in connector_class(FixturePageFetcher(str(FIXTURES))).build_url(query)


def test_auctions_cannot_be_rented():
    connector = KomornikConnector(FixturePageFetcher(str(FIXTURES)))
    assert not connector.supports(DealType.RENT, PropertyType.FLAT)
    assert connector.build_url(SearchQuery(place=KRAKOW, deal_type=DealType.RENT)) is None



def test_a_village_with_a_radius():
    zabierzow = known_place("zabierzow")
    query = SearchQuery(place=zabierzow, max_price=600000, min_area=40, radius_km=25)
    fetcher = FixturePageFetcher(str(FIXTURES))
    otodom = OtodomConnector(fetcher).build_url(query)
    assert "/sprzedaz/mieszkanie/malopolskie/krakowski/zabierzow/zabierzow?distanceRadius=25&" in otodom
    assert "/mieszkania/sprzedaz/zabierzow/?search%5Bdist%5D=30&" in OlxConnector(fetcher).build_url(query)  # OLX has no 25
    assert "morizon.pl/mieszkania/najnowsze/zabierzow/" in MorizonConnector(fetcher).build_url(query)
    assert "city=Zabierz%C3%B3w" in KomornikConnector(fetcher).build_url(query)


def test_market_seller_and_floors_go_into_each_portals_address():
    fetcher = FixturePageFetcher(str(FIXTURES))
    query = SearchQuery(place=KRAKOW, market=Market.SECONDARY, private_only=True, min_floor=2, max_floor=3)
    otodom = OtodomConnector(fetcher).build_url(query)
    assert otodom.endswith("&market=SECONDARY&ownerTypeSingleSelect=PRIVATE&floors=%5BSECOND%2CTHIRD%5D")
    olx = OlxConnector(fetcher).build_url(query)
    assert "&search%5Bfilter_enum_market%5D%5B0%5D=secondary&search%5Bprivate_business%5D=private" in olx
    assert olx.endswith("%5B0%5D=floor_2&search%5Bfilter_enum_floor_select%5D%5B1%5D=floor_3")
    # Morizon cannot show private sellers only, and a bailiff never sells as the owner: both sit this one out.
    assert MorizonConnector(fetcher).build_url(query) is None
    assert KomornikConnector(fetcher).build_url(query) is None

    new_builds = SearchQuery(place=KRAKOW, market=Market.PRIMARY, min_floor=1)
    assert MorizonConnector(fetcher).build_url(new_builds).endswith("&ps%5Bmarket_type%5D=1&ps%5Bfloor_from%5D=1")
    assert KomornikConnector(fetcher).build_url(new_builds) is None  # no new builds at an auction


def test_an_open_floor_range_reaches_the_top():
    url = OtodomConnector(FixturePageFetcher(str(FIXTURES))).build_url(SearchQuery(place=KRAKOW, min_floor=9))
    assert url.endswith("&floors=%5BNINTH%2CTENTH%2CABOVE_TENTH%2CGARRET%5D")


def test_otodom_and_morizon_read_the_floor():
    item = {"id": 1, "slug": "a-1", "title": "2 pokoje", "floorNumber": "GROUND", "isPrivateOwner": True}
    html = '<script id="__NEXT_DATA__">' + json.dumps({"props": {"pageProps": {"data": {"searchAds": {"items": [item]}}}}}) + "</script>"
    listing = next(iter(OtodomConnector(FixturePageFetcher(str(FIXTURES))).parse(html)))
    assert (listing.floor, listing.private) == (0, True)
    assert [MorizonConnector._floor(text) for text in ("piętro 3/10", "parter/4", "parter", None)] == [3, 0, 0, None]


@pytest.mark.parametrize(
    ("connector_class", "deal", "kind", "expected"),
    [
        (OtodomConnector, DealType.RENT, PropertyType.ROOM, "otodom.pl/pl/wyniki/wynajem/pokoj/malopolskie/"),
        (OtodomConnector, DealType.SALE, PropertyType.PLOT, "otodom.pl/pl/wyniki/sprzedaz/dzialka/"),
        (OtodomConnector, DealType.RENT, PropertyType.COMMERCIAL, "otodom.pl/pl/wyniki/wynajem/lokal/"),
        (OlxConnector, DealType.RENT, PropertyType.ROOM, "olx.pl/nieruchomosci/stancje-pokoje/krakow/?search%5Bdist%5D=0&"),
        (OlxConnector, DealType.SALE, PropertyType.PLOT, "olx.pl/nieruchomosci/dzialki/sprzedaz/krakow/"),
        (OlxConnector, DealType.SALE, PropertyType.COMMERCIAL, "olx.pl/nieruchomosci/biura-lokale/sprzedaz/krakow/"),
        (MorizonConnector, DealType.RENT, PropertyType.ROOM, "morizon.pl/do-wynajecia/pokoje/najnowsze/krakow/"),
        (MorizonConnector, DealType.SALE, PropertyType.PLOT, "morizon.pl/dzialki/najnowsze/krakow/"),
        (MorizonConnector, DealType.RENT, PropertyType.COMMERCIAL, "morizon.pl/do-wynajecia/komercyjne/najnowsze/krakow/"),
        (KomornikConnector, DealType.SALE, PropertyType.PLOT, "subCategory=LAND&"),
        (KomornikConnector, DealType.SALE, PropertyType.COMMERCIAL, "subCategory=COMMERCIAL_PREMISESISES&"),
    ],
)
def test_rooms_plots_and_commercial_units(connector_class, deal, kind, expected):
    """Addresses checked against each portal; rooms are only rented and plots only sold."""
    query = SearchQuery(place=KRAKOW, deal_type=deal, property_type=kind)
    assert expected in connector_class(FixturePageFetcher(str(FIXTURES))).build_url(query)


def test_no_portal_sells_rooms_or_rents_out_plots():
    fetcher = FixturePageFetcher(str(FIXTURES))
    for connector_class in (OtodomConnector, OlxConnector, MorizonConnector, KomornikConnector):
        connector = connector_class(fetcher)
        assert not connector.supports(DealType.SALE, PropertyType.ROOM)
        assert not connector.supports(DealType.RENT, PropertyType.PLOT)
