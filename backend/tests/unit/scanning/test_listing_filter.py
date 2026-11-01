from app.services.connectors.models import Listing
from app.services.scanning.listing_filter import ListingFilter
from tests.unit.conftest import make_search


def listing(**overrides) -> Listing:
    values = dict(source="otodom", external_id="1", url="u", title="2 pokoje", price=500000, area=45.0)
    values.update(overrides)
    return Listing(**values)


def test_accepts_a_listing_within_budget():
    assert ListingFilter(make_search()).accepts(listing())


def test_rejects_over_budget_and_too_small():
    rules = ListingFilter(make_search(max_price=500000, min_area=40))
    assert rules.reason_to_reject(listing(price=500001)) == "price 500001 > 500000"
    assert rules.reason_to_reject(listing(area=39.9)).startswith("area")


def test_unpriced_listing_cannot_pass_a_budget_check():
    assert ListingFilter(make_search()).reason_to_reject(listing(price=None)) == "no price published"


def test_missing_area_does_not_reject():
    assert ListingFilter(make_search()).accepts(listing(area=None))


def test_reject_keywords_match_inflected_forms():
    rules = ListingFilter(make_search(reject_keywords=["udział"]))
    assert not rules.accepts(listing(title="Sprzedam 1/2 udziału w mieszkaniu"))


def test_rooms_range():
    rules = ListingFilter(make_search(min_rooms=2, max_rooms=3))
    assert rules.reason_to_reject(listing(rooms=1)) == "rooms 1 < 2"
    assert rules.reason_to_reject(listing(rooms=4)) == "rooms 4 > 3"
    assert rules.accepts(listing(rooms=None))  # unknown never rejects


def test_price_per_square_metre():
    rules = ListingFilter(make_search(max_price_per_m2=10000))
    assert rules.accepts(listing(price=450000, area=45.0))
    assert rules.reason_to_reject(listing(price=500000, area=45.0)) == "11111 zł/m² > 10000"


def test_minimum_price_filters_out_placeholders():
    assert not ListingFilter(make_search(min_price=1000)).accepts(listing(price=1))


def test_required_keywords_must_be_present():
    rules = ListingFilter(make_search(required_keywords=["balkon"]))
    assert rules.accepts(listing(title="2 pokoje z balkonem"))
    assert rules.reason_to_reject(listing(title="2 pokoje")).startswith("missing required keyword")
