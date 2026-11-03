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


def test_a_garage_or_a_shop_is_not_a_home_but_a_flat_with_a_garage_is():
    rules = ListingFilter(make_search(reject_keywords=[]))
    for title in ("GARAŻ - 17m2 - ZAMKNIĘTE OSIEDLE", "Miejsce postojowe w hali", "Lokal użytkowy na parterze"):
        assert rules.reason_to_reject(listing(title=title)).startswith("not a home"), title
    for title in ("Bezpośrednio | 62m² + Garaż", "Hala Garażowa W CENIE -> 2 pokoje", "Lokal na ostatnim piętrze"):
        assert rules.accepts(listing(title=title)), title


def test_a_rejected_word_also_catches_its_other_spelling():
    rules = ListingFilter(make_search(reject_keywords=["suterena"]))
    assert not rules.accepts(listing(title="2 pokoje | Wola Duchacka | Suteryna"))


def test_a_flat_sold_with_its_tenant_is_left_out_by_default():
    assert not ListingFilter(make_search()).accepts(listing(title="DWA MIESZKANIA NA WYNAJEM, Z NAJEMCAMI"))


def test_floors_and_private_sellers():
    rules = ListingFilter(make_search(min_floor=1, max_floor=4, private_only=True))
    assert rules.reason_to_reject(listing(floor=0)) == "floor 0 < 1"
    assert rules.reason_to_reject(listing(floor=5)) == "floor 5 > 4"
    assert rules.accepts(listing(floor=None))  # a floor the portal did not publish rejects nothing
    assert rules.reason_to_reject(listing(floor=2, private=False)) == "not from the owner"
    assert rules.accepts(listing(floor=2, private=True))


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


def test_required_keywords_must_be_present_in_a_known_description():
    rules = ListingFilter(make_search(required_keywords=["balkon"]))
    assert rules.accepts(listing(title="2 pokoje", description="Duży balkon od południa"))
    assert rules.reason_to_reject(listing(title="2 pokoje", description="Bez windy")) == "missing required keyword balkon"


def test_a_title_alone_cannot_prove_a_word_is_missing():
    # Results pages (Morizon, OLX) show only a title: a house in Oświęcim was lost this way.
    assert ListingFilter(make_search(required_keywords=["Balkon"])).accepts(listing(title="Dom wolnostojący"))


def test_rejections_are_named_for_the_search_card():
    from app.services.scanning.listing_filter import reason_code

    assert reason_code("keyword TBS") == "reject:TBS"
    assert reason_code("missing required keyword balkon") == "missing:balkon"
    assert reason_code("price 500001 > 500000") == "price"
    assert reason_code("no price published") == "price"
    assert reason_code("11111 zł/m² > 10000") == "per_m2"
    assert reason_code("area 30 < 40") == "area"
    assert reason_code("floor 0 < 1") == "floor"
