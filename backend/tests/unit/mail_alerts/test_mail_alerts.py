from dataclasses import replace
from pathlib import Path

import pytest

from app.core.container import Container
from app.services.connectors.models import DealType
from app.services.mail_alerts.inbox import FolderInbox
from app.services.places.known import known_place
from tests.unit.conftest import ADMIN_EMAIL, make_search

MAIL = Path(__file__).parents[2] / "fixtures" / "mail"


@pytest.fixture
def mail_container(settings, clock, telegram):
    return Container(replace(settings, mail_alerts_dir=str(MAIL)), clock=clock, telegram_client=telegram,
                     background=lambda task, *args: task(*args))


def owner_with_chat(container, **search):
    owner = container.auth.sign_in("dev", ADMIN_EMAIL).user
    token = container.telegram_links.create_link(owner).token
    container.telegram_dispatcher.handle({"message": {"text": f"/start {token}", "chat": {"id": 900, "title": "me"}}})
    found = container.searches.create(owner, make_search(name="Mail", sources=["otodom", "olx", "morizon"], **search))
    return owner, found


def test_alert_emails_reach_the_owner_through_filters_storage_and_telegram(mail_container, telegram):
    owner, search = owner_with_chat(mail_container, max_price=600000, min_area=25)
    telegram.outbox.clear()
    status = mail_container.mail_alerts.check()
    assert (status.state, status.mails, status.offers) == ("ok", 2, 4)
    stored = {item.key for item in mail_container.listings.latest(owner, search.id)}
    # 649 000 and 1 190 000 are over the limit; the other two pass.
    assert {"olx:Qw34Cd", "otodom:4uAb1"} <= stored and "olx:Xy12Ab" not in stored and "otodom:4uCd2" not in stored
    photos = [message for message in telegram.outbox if message.photo]
    assert photos and all(message.chat_id == "900" for message in telegram.outbox)
    assert any("Kawalerka przy AGH" in message.text for message in telegram.outbox)


class ReadOnce(FolderInbox):
    """Like a real mailbox: what was marked read is not offered again."""

    def __init__(self, folder):
        super().__init__(folder)
        self.read: set[str] = set()

    def unread_from(self, domains):
        return [mail for mail in super().unread_from(domains) if mail.uid not in self.read]

    def mark_read(self, uids):
        self.read.update(uids)


def test_each_email_is_read_once(mail_container, telegram):
    owner_with_chat(mail_container)
    mail_container.mail_alerts._inbox = ReadOnce(str(MAIL))
    assert mail_container.mail_alerts.check().mails == 2
    sent = len(telegram.outbox)
    second = mail_container.mail_alerts.check()
    assert second.mails == 0 and len(telegram.outbox) == sent
    assert second.totals["mails"] == 2


def test_an_offer_already_known_is_not_announced_again(mail_container, telegram):
    owner, search = owner_with_chat(mail_container)
    mail_container.mail_alerts.check()
    again = mail_container.mail_alerts.check()  # the same emails seen again
    assert again.offers == 4 and again.new == 0 and again.sent == 0


def test_other_users_never_get_offers_from_the_owners_mailbox(mail_container, sign_in, telegram):
    owner_with_chat(mail_container)
    someone = sign_in("someone@example.com")
    mail_container.searches.create(someone, make_search(sources=["otodom", "olx"]))
    mail_container.mail_alerts.check()
    assert mail_container.listings.latest(someone) == []


def test_the_email_goes_to_the_search_for_the_place_it_names(mail_container, settings):
    owner, krakow = owner_with_chat(mail_container)
    katowice = mail_container.searches.create(owner, make_search(
        name="Katowice", place=known_place("katowice"), sources=["olx", "otodom"],
    ))
    mail_container.mail_alerts.check()
    assert mail_container.listings.latest(owner, krakow.id)
    assert mail_container.listings.latest(owner, katowice.id) == []


def test_a_search_without_the_portal_gets_nothing(mail_container):
    owner = mail_container.auth.sign_in("dev", ADMIN_EMAIL).user
    only_morizon = mail_container.searches.create(owner, make_search(sources=["morizon"]))
    status = mail_container.mail_alerts.check()
    assert status.offers == 4 and status.new == 0
    assert mail_container.listings.latest(owner, only_morizon.id) == []


def test_without_the_owners_account_emails_wait_unread(mail_container):
    status = mail_container.mail_alerts.check()
    assert status.state == "error" and ADMIN_EMAIL in status.error
    assert mail_container.mail_alerts.public_state == "error (the owner has no account)"  # no address published
    owner_with_chat(mail_container)
    assert mail_container.mail_alerts.check().mails == 2  # still there once the owner signs up


def test_a_mailbox_failure_is_reported_and_scanning_goes_on(mail_container):
    owner_with_chat(mail_container)

    class Broken:
        address = "x"

        def unread_from(self, domains):
            raise OSError("connection refused")

    mail_container.mail_alerts._inbox = Broken()
    status = mail_container.mail_alerts.check()
    assert status.state == "error" and "connection refused" in status.error
    assert mail_container.mail_alerts.public_state == "error (OSError)"
    assert mail_container.scanner.run().searches_scanned >= 0


def test_a_mailbox_is_ok_only_once_it_was_read(mail_container):
    owner_with_chat(mail_container)
    assert mail_container.mail_alerts.status.state == "waiting"
    assert mail_container.mail_alerts.check().state == "ok"


def test_no_mailbox_means_off(container):
    assert container.mail_alerts.status.state == "off"
    container.mail_alerts.run_if_due()  # does nothing, raises nothing


def test_checks_run_every_few_minutes(mail_container, clock):
    owner_with_chat(mail_container)
    mail_container.mail_alerts.run_if_due()
    checked = mail_container.mail_alerts.status.checked_at
    clock.advance(minutes=2)
    mail_container.mail_alerts.run_if_due()
    assert mail_container.mail_alerts.status.checked_at == checked
    clock.advance(minutes=4)
    mail_container.mail_alerts.run_if_due()
    assert mail_container.mail_alerts.status.checked_at != checked


def test_rentals_and_houses_still_filter_by_their_own_rules(mail_container):
    owner, rent = owner_with_chat(mail_container, deal_type=DealType.RENT, max_price=4000)
    mail_container.mail_alerts.check()
    assert mail_container.listings.latest(owner, rent.id) == []  # every offer in the emails costs far more


def test_the_mailbox_defaults_to_the_smtp_login(settings):
    smtp = replace(settings, smtp_host="smtp.gmail.com", smtp_username="me@gmail.com", smtp_password="app-pass")
    assert smtp.alert_mailbox == ("imap.gmail.com", 993, "me@gmail.com", "app-pass")
    assert replace(smtp, mail_alerts_imap_host="imap.other.pl").alert_mailbox[0] == "imap.other.pl"
    assert replace(settings, smtp_host="mail.example.com", smtp_username="a", smtp_password="b").alert_mailbox is None
    assert settings.alert_owner == ADMIN_EMAIL
    spaced = replace(smtp, smtp_password="abcd efgh ijkl mnop")
    assert spaced.alert_mailbox[3] == "abcdefghijklmnop"  # as Google shows it, without the spaces


def test_the_published_reason_names_the_failure_not_the_mailbox():
    import imaplib
    import socket

    from app.services.mail_alerts.service import _reason

    assert _reason(imaplib.IMAP4.error("b'[AUTHENTICATIONFAILED] Invalid credentials (Failure)'")) == "wrong username or password"
    app_password = "b'[ALERT] Application-specific password required: https://support.google.com/accounts/answer/185833'"
    assert _reason(imaplib.IMAP4.error(app_password)) == "Gmail wants an app password"
    assert _reason(imaplib.IMAP4.error("b'[ALERT] Your account is not enabled for IMAP use.'")) == "IMAP is off in Gmail"
    assert _reason(imaplib.IMAP4.error("b'[ALERT] Please log in via your web browser'")).startswith("Google blocked")
    assert _reason(imaplib.IMAP4.error("b'LOGIN failed'")) == "login refused"
    assert _reason(socket.gaierror(8, "nodename nor servname provided")) == "mail host not found"
    assert _reason(TimeoutError()) == "mail host did not answer"
