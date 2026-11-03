import pytest

from app.core.errors import Invalid, LimitReached, NotFound
from app.services.billing.plans import PRO
from app.services.places.models import Place
from tests.unit.conftest import make_search


def test_free_plan_allows_one_search(container, sign_in):
    user = sign_in()
    container.searches.create(user, make_search())
    with pytest.raises(LimitReached):
        container.searches.create(user, make_search(name="second"))


def test_pro_only_portal_is_locked_on_free(container, sign_in):
    user = sign_in()
    with pytest.raises(LimitReached, match="komornik"):
        container.searches.create(user, make_search(sources=["komornik"]))
    container.users.set_plan(user.id, PRO)
    assert container.searches.create(container.users.get(user.id), make_search(sources=["komornik"]))


def test_validation(container, sign_in):
    user = sign_in()
    with pytest.raises(Invalid):
        container.searches.create(user, make_search(place=Place("Berlin", "berlin/berlin/berlin/berlin", "Berlin", 52.52, 13.40)))
    with pytest.raises(Invalid):
        container.searches.create(user, make_search(radius_km=7))
    with pytest.raises(Invalid):
        container.searches.create(user, make_search(min_area=50, max_area=40))
    with pytest.raises(Invalid):
        container.searches.create(user, make_search(sources=[]))


def test_editing_a_search_makes_it_due_again(container, sign_in):
    user = sign_in()
    search = container.searches.create(user, make_search())
    container.scanner.run()
    assert container.searches.due(user) == []
    container.searches.update(user, search.id, make_search(max_price=500000))
    assert [s.id for s in container.searches.due(user)] == [search.id]


def test_users_cannot_see_each_others_searches(container, sign_in):
    search = container.searches.create(sign_in("anna@x.pl"), make_search())
    with pytest.raises(NotFound):
        container.searches.get(sign_in("ben@x.pl"), search.id)


def test_portal_that_cannot_search_this_deal_is_refused(container, sign_in):
    from app.services.connectors.models import DealType

    user = sign_in()
    container.users.set_plan(user.id, PRO)
    with pytest.raises(Invalid, match="komornik has no flat listings to rent") as refused:
        container.searches.create(container.users.get(user.id), make_search(deal_type=DealType.RENT, sources=["komornik"]))
    # The words inside the message are translated too, not left as English codes.
    assert "квартира" in refused.value.text("uk") and "оренда" in refused.value.text("uk")


def test_new_fields_round_trip(container, sign_in):
    from app.services.connectors.models import DealType, PropertyType

    user = sign_in()
    created = container.searches.create(user, make_search(
        deal_type=DealType.RENT, property_type=PropertyType.HOUSE, min_rooms=2, max_rooms=4,
        max_price_per_m2=80, required_keywords=["ogród"], max_price=6000,
    ))
    stored = container.searches.get(user, created.id)
    assert (stored.deal_type, stored.property_type, stored.min_rooms, stored.required_keywords) == (
        DealType.RENT, PropertyType.HOUSE, 2, ["ogród"])


def test_scan_interval_must_be_offered_and_allowed_by_the_plan(container, sign_in):
    user = sign_in()
    with pytest.raises(Invalid):
        container.searches.create(user, make_search(interval_minutes=7))
    with pytest.raises(LimitReached, match="every 1440 minutes"):
        container.searches.create(user, make_search(interval_minutes=60))
    with pytest.raises(LimitReached):
        container.searches.create(user, make_search(interval_minutes=5))
    assert container.searches.create(user, make_search(interval_minutes=1440)).interval_minutes == 1440


def test_new_search_is_scanned_daily_by_default(container, sign_in):
    assert container.searches.create(sign_in(), make_search()).interval_minutes == 1440
