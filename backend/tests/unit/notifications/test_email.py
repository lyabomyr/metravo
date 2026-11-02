"""Listings by email: switch it on, check it with a test message, switch it off."""

import pytest

from app.core.errors import Invalid
from app.services.billing.plans import PRO
from tests.unit.conftest import make_search
from tests.unit.scanning.test_scan_service import link_telegram


def pro(container, sign_in, email="anna@example.com"):
    user = sign_in(email)
    container.users.set_plan(user.id, PRO)
    return container.users.get(user.id)


def test_email_is_live_when_a_mailer_is_configured(client):
    token = client.post("/api/auth/session", json={"provider": "dev", "credential": "ola@x.pl"}).json()["token"]
    channels = client.get("/api/notifications/channels", headers={"Authorization": f"Bearer {token}"}).json()
    assert {c["code"]: c["live"] for c in channels} == {
        "telegram": True, "email": True, "whatsapp": False, "viber": False, "signal": False,
    }


def test_new_listings_arrive_by_email(container, sign_in):
    user = pro(container, sign_in)
    container.notifications.update(user, "email", True, "flats@anna.pl")
    container.searches.create(user, make_search(name="Kraków 2 rooms"))

    container.scanner.run()

    [mail] = container.mailer.outbox
    assert mail.to == "flats@anna.pl"
    assert "Kraków 2 rooms" in mail.subject and "4" in mail.subject
    assert 'href="https://www.otodom.pl/' in mail.html
    assert "/alerts" in mail.html  # how to switch it off


def test_email_comes_in_the_users_language(container, sign_in):
    user = pro(container, sign_in)
    container.users.set_locale(user, "uk")
    container.notifications.update(container.users.get(user.id), "email", True, "anna@example.com")
    container.searches.create(container.users.get(user.id), make_search(name="Квартира"))
    container.scanner.run()
    assert "нових" in container.mailer.outbox[0].subject


def test_an_address_that_is_not_an_email_is_refused(container, sign_in):
    user = pro(container, sign_in)
    with pytest.raises(Invalid):
        container.notifications.update(user, "email", True, "anna at example")


def test_switching_email_off_stops_it(container, sign_in):
    user = pro(container, sign_in)
    container.notifications.update(user, "email", True, "anna@example.com")
    container.notifications.update(user, "email", False, "anna@example.com")
    container.searches.create(user, make_search())
    container.scanner.run()
    assert container.mailer.outbox == []


def test_a_test_message_proves_the_channel_works(container, sign_in, telegram):
    user = pro(container, sign_in)
    container.notifications.update(user, "email", True, "flats@anna.pl")
    container.notifier.send_test(user, "email")
    assert container.mailer.outbox[-1].to == "flats@anna.pl"

    link_telegram(container, user, "42")
    container.notifier.send_test(user, "telegram")
    assert telegram.outbox[-1].chat_id == "42"


def test_a_test_message_needs_the_channel_switched_on(container, sign_in):
    user = pro(container, sign_in)
    with pytest.raises(Invalid):
        container.notifier.send_test(user, "email")  # still off
    with pytest.raises(Invalid):
        container.notifier.send_test(user, "telegram")  # no chat yet


def test_test_message_api(client, container):
    token = client.post("/api/auth/session", json={"provider": "dev", "credential": "ola@x.pl"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    user = container.users.by_email("ola@x.pl")
    container.users.set_plan(user.id, PRO)
    client.put("/api/notifications/channels/email", json={"enabled": True, "address": "ola@x.pl"}, headers=headers)
    assert client.post("/api/notifications/channels/email/test", headers=headers).status_code == 204
    assert container.mailer.outbox[-1].to == "ola@x.pl"
