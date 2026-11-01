"""Each connector parses its saved fixture page into the expected listings."""

import pytest

from app.services.connectors.fetchers import FixturePageFetcher
from app.services.connectors.komornik.connector import KomornikConnector
from app.services.connectors.models import DealType, PropertyType, SearchQuery
from app.services.connectors.morizon.connector import MorizonConnector
from app.services.connectors.olx.connector import OlxConnector
from app.services.connectors.otodom.connector import OtodomConnector
from tests.unit.conftest import FIXTURES

QUERY = SearchQuery(city="krakow", max_price=610000, min_area=39)


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
         "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/malopolskie/krakow/krakow/krakow?priceMax=610000&areaMin=39"),
        (OtodomConnector, DealType.RENT, PropertyType.HOUSE, "/pl/wyniki/wynajem/dom/malopolskie/"),
        (OlxConnector, DealType.RENT, PropertyType.FLAT, "/nieruchomosci/mieszkania/wynajem/krakow/"),
        (MorizonConnector, DealType.RENT, PropertyType.FLAT, "morizon.pl/do-wynajecia/mieszkania/najnowsze/krakow/"),
        (MorizonConnector, DealType.SALE, PropertyType.HOUSE, "morizon.pl/domy/najnowsze/krakow/"),
        (KomornikConnector, DealType.SALE, PropertyType.FLAT, "subCategory=APARTMENTS&province=ma%C5%82opolskie&city=Krak%C3%B3w"),
        (KomornikConnector, DealType.SALE, PropertyType.HOUSE, "subCategory=HOUSES"),
    ],
)
def test_urls_are_built_from_the_search(connector_class, deal, kind, expected):
    query = SearchQuery(city="krakow", deal_type=deal, property_type=kind, max_price=610000, min_area=39)
    assert expected in connector_class(FixturePageFetcher(str(FIXTURES))).build_url(query)


def test_auctions_cannot_be_rented():
    connector = KomornikConnector(FixturePageFetcher(str(FIXTURES)))
    assert not connector.supports(DealType.RENT, PropertyType.FLAT)
    assert connector.build_url(SearchQuery(city="krakow", deal_type=DealType.RENT)) is None
