"""Free is a one-week trial: everything works for seven days, then checks and alerts pause."""

import pytest

from app.core.errors import LimitReached
from app.services.billing.plans import PRO
from tests.unit.conftest import ADMIN_EMAIL, make_search
from tests.unit.scanning.test_scan_service import link_telegram


def test_free_works_for_a_week_then_pauses(container, sign_in, clock, telegram):
    user = sign_in()
    link_telegram(container, user)
    container.searches.create(user, make_search())
    assert container.users.free_until(user) is not None and container.users.is_active(user)

    clock.advance(days=6, hours=23)
    assert container.scanner.run().searches_scanned == 1
    sent = len(telegram.outbox)

    clock.advance(hours=2)  # past the seventh day
    assert not container.users.is_active(user)
    assert container.scanner.run().searches_scanned == 0
    assert len(telegram.outbox) == sent


def test_after_the_week_new_searches_and_check_now_are_refused(container, sign_in, clock):
    user = sign_in()
    clock.advance(days=8)
    with pytest.raises(LimitReached, match="free week"):
        container.searches.create(user, make_search())
    with pytest.raises(LimitReached):
        container.scanner.check_now(user)


def test_pro_and_admins_have_no_end_date(container, sign_in, clock):
    customer = sign_in("anna@x.pl")
    container.users.set_plan(customer.id, PRO)
    admin = sign_in(ADMIN_EMAIL)
    clock.advance(days=30)
    for user in (container.users.get(customer.id), container.users.get(admin.id)):
        assert container.users.free_until(user) is None and container.users.is_active(user)


def test_the_site_is_told_how_long_is_left(client, clock):
    token = client.post("/api/auth/session", json={"provider": "dev", "credential": "ola@x.pl"}).json()["token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["active"] is True and me["free_until"].startswith("2026-11-08")
