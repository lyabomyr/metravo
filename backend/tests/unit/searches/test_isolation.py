"""Everyone's searches and listings share one database; nobody sees anyone else's."""

import pytest

from app.core.errors import NotFound
from tests.unit.conftest import make_search


def test_a_user_sees_only_their_own_searches_and_listings(container, sign_in):
    anna, ben = sign_in("anna@x.pl"), sign_in("ben@x.pl")
    annas = container.searches.create(anna, make_search())
    container.scanner.run()

    assert container.searches.list(ben) == []
    assert container.listings.latest(ben) == []
    assert container.listings.latest(ben, search_id=annas.id) == []
    assert len(container.listings.latest(anna)) == 4


def test_a_search_cannot_be_read_changed_or_deleted_by_someone_else(container, sign_in):
    anna, ben = sign_in("anna@x.pl"), sign_in("ben@x.pl")
    annas = container.searches.create(anna, make_search())

    with pytest.raises(NotFound):
        container.searches.get(ben, annas.id)
    with pytest.raises(NotFound):
        container.searches.update(ben, annas.id, make_search(name="taken"))
    with pytest.raises(NotFound):
        container.searches.delete(ben, annas.id)
    assert container.searches.get(anna, annas.id).name == annas.name


def test_plan_limits_count_only_the_users_own_searches(container, sign_in):
    anna, ben = sign_in("anna@x.pl"), sign_in("ben@x.pl")
    container.searches.create(anna, make_search())
    container.searches.create(ben, make_search())  # Free allows one each
