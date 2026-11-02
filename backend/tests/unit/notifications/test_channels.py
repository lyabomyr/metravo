import pytest

from app.core.errors import Invalid, LimitReached, NotFound
from app.services.billing.plans import PRO
from app.services.notifications.notifier import FanOutNotifier
from app.services.notifications.senders.base import ChannelSender


def channel(settings, code):
    return next(setting for setting in settings if setting.channel.code == code)


def test_free_users_get_telegram_and_see_the_pro_channels_locked(container, sign_in):
    settings = container.notifications.settings(sign_in())
    assert channel(settings, "telegram").enabled and channel(settings, "telegram").allowed
    assert not channel(settings, "whatsapp").allowed
    assert channel(settings, "email").address == "anna@example.com"  # the account's email by default


def test_pro_channels_need_pro_and_an_address(container, sign_in):
    user = sign_in()
    with pytest.raises(LimitReached, match="WhatsApp"):
        container.notifications.update(user, "whatsapp", True, "+48 600 000 000")
    container.users.set_plan(user.id, PRO)
    pro = container.users.get(user.id)
    with pytest.raises(Invalid):
        container.notifications.update(pro, "viber", True, " ")
    with pytest.raises(NotFound):
        container.notifications.update(pro, "pigeon", True, "")
    saved = container.notifications.update(pro, "whatsapp", True, "+48 600 000 000")
    assert saved.enabled and saved.address == "+48 600 000 000"


def test_listings_go_to_every_switched_on_channel_that_has_a_sender(container, sign_in):
    user = sign_in()
    container.users.set_plan(user.id, PRO)
    pro = container.users.get(user.id)
    container.notifications.update(pro, "email", True, "anna@example.com")
    container.notifications.update(pro, "whatsapp", True, "+48 600")

    class Recording(ChannelSender):
        def __init__(self, code):
            self.channel, self.calls = code, []

        def deliver(self, user, address, search, events):
            self.calls.append(address)
            return 1

    telegram, email = Recording("telegram"), Recording("email")
    sent = FanOutNotifier(container.notifications, [telegram, email]).notify(pro, None, [])
    assert sent == 2  # whatsapp has no sender yet: kept, skipped
    assert email.calls == ["anna@example.com"]


def test_a_downgrade_stops_pro_channels(container, sign_in):
    user = sign_in()
    container.users.set_plan(user.id, PRO)
    container.notifications.update(container.users.get(user.id), "email", True, "a@b.pl")
    container.users.set_plan(user.id, "free")
    assert [s.channel.code for s in container.notifications.active(container.users.get(user.id))] == ["telegram"]


def test_channels_api(client):
    token = client.post("/api/auth/session", json={"provider": "dev", "credential": "ola@x.pl"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    codes = [c["code"] for c in client.get("/api/notifications/channels", headers=headers).json()]
    assert codes == ["telegram", "email", "whatsapp", "viber", "signal"]
    response = client.put("/api/notifications/channels/signal", json={"enabled": True, "address": "+48"}, headers=headers)
    assert response.status_code == 402
