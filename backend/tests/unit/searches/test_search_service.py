import pytest

from app.core.errors import Invalid, LimitReached, NotFound
from app.services.billing.plans import PRO
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
        container.searches.create(user, make_search(city="berlin"))
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
