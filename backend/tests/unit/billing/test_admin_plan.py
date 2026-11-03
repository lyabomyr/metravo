from app.services.billing.plans import PRO
from tests.unit.conftest import ADMIN_EMAIL, make_search


def test_an_admin_has_pro_without_paying(container, sign_in):
    admin = sign_in(ADMIN_EMAIL)
    assert admin.plan == PRO and admin.is_admin
    assert container.users.plan_of(admin).min_interval_minutes == 60


def test_an_admin_search_is_checked_every_hour(container, sign_in, clock):
    admin = sign_in(ADMIN_EMAIL)
    container.searches.create(admin, make_search(interval_minutes=60))
    assert container.scanner.run().searches_scanned == 1
    clock.advance(minutes=61)
    assert container.scanner.run().searches_scanned == 1


def test_everyone_else_keeps_their_own_plan(sign_in):
    assert sign_in("someone@example.com").plan == "free"
