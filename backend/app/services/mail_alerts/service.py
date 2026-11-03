from __future__ import annotations

import imaplib
import socket
from dataclasses import dataclass, field
from datetime import timedelta

from ...core.clock import Clock, parse_iso
from ...core.service import BaseService
from ..connectors.models import Listing
from ..places.models import slugify
from ..scanning.service import ScanService
from ..searches.models import Search
from ..searches.service import SearchService
from ..users.models import User
from ..users.service import UserService
from .inbox import AlertMail, Inbox
from .parser import SENDER_DOMAINS, AlertParser


@dataclass
class MailAlertStatus:
    #: "off" (no mailbox configured), "waiting" (not opened yet), "ok" (read successfully) or "error".
    state: str = "off"
    mailbox: str = ""
    owner: str = ""
    checked_at: str | None = None
    #: The last check, and everything since the server started.
    mails: int = 0
    offers: int = 0
    new: int = 0
    sent: int = 0
    totals: dict[str, int] = field(default_factory=lambda: {"mails": 0, "offers": 0, "new": 0, "sent": 0})
    error: str | None = None
    #: The error in a few words that name no mailbox or person — safe to publish.
    reason: str | None = None


class MailAlertService(BaseService):
    """OLX and Otodom offers from the portals' own alert emails (saved searches).

    The emails reach one mailbox, so their offers go to that mailbox's owner
    only — through the owner's searches that include the portal, with the
    same filters, storage and Telegram routes as a scan. The scan's other
    sources are untouched.
    """

    def __init__(self, inbox: Inbox | None, parser: AlertParser, users: UserService, searches: SearchService,
                 scanner: ScanService, owner_email: str, clock: Clock, every: timedelta = timedelta(minutes=5)):
        super().__init__()
        self._inbox, self._parser = inbox, parser
        self._users, self._searches, self._scanner = users, searches, scanner
        self._clock, self._every = clock, every
        self.status = MailAlertStatus(state="off" if inbox is None else "waiting",
                                      mailbox=inbox.address if inbox else "", owner=owner_email)

    def run_if_due(self) -> None:
        last = self.status.checked_at
        if self._inbox and (last is None or self._clock.now() - parse_iso(last) >= self._every):
            self.check()

    def check(self) -> MailAlertStatus:
        status = self.status
        status.checked_at = self._clock.iso()
        if self._inbox is None:
            return status
        owner = self._users.by_email(status.owner) if status.owner else None
        if owner is None:
            status.state, status.error = "error", f"no Metravo account for the owner {status.owner or '(not set)'}"
            status.reason = "the owner has no account"
            return status  # emails stay unread until the owner signs up
        try:
            mails = self._inbox.unread_from(SENDER_DOMAINS)
            counts = [self._deliver(owner, mail) for mail in mails]
            self._inbox.mark_read([mail.uid for mail in mails])
        except Exception as error:  # noqa: BLE001 — a mailbox outage must not stop scanning
            self.log.warning("alert mailbox check failed: %s", error)
            status.state, status.error, status.reason = "error", f"{type(error).__name__}: {error}"[:300], _reason(error)
            return status
        status.state, status.error, status.reason = "ok", None, None
        status.mails = len(mails)
        status.offers, status.new, status.sent = (sum(column) for column in zip(*counts, strict=False)) if counts else (0, 0, 0)
        for key in ("mails", "offers", "new", "sent"):
            status.totals[key] += getattr(status, key)
        if mails:
            self.log.info("alert emails: %s read, %s offers, %s new, %s messages", status.mails, status.offers, status.new, status.sent)
        return status

    def _deliver(self, owner: User, mail: AlertMail) -> tuple[int, int, int]:
        listings = self._parser.listings(mail)
        new = sent = 0
        for search in self._targets(owner, mail, listings):
            report = self._scanner.ingest(owner, search, [item for item in listings if item.source in search.sources])
            new, sent = new + report.new_listings, sent + report.messages_sent
        return len(listings), new, sent

    @property
    def public_state(self) -> str:
        return f"{self.status.state} ({self.status.reason})" if self.status.reason else self.status.state

    def _targets(self, owner: User, mail: AlertMail, listings: list[Listing]) -> list[Search]:
        """The owner's searches for these portals; those whose place the email names, when any does."""
        sources = {listing.source for listing in listings}
        searches = [search for search in self._searches.list(owner) if search.enabled and sources & set(search.sources)]
        words = f"-{slugify(f'{mail.subject} {mail.text} {mail.html}')}-"
        named = [search for search in searches if any(f"-{slugify(place.name)}-" in words for place in search.places)]
        return named or searches


# What Gmail says when it refuses an IMAP login, and what that means for the person fixing it.
_GMAIL_REFUSALS = (
    ("application-specific password required", "Gmail wants an app password"),
    ("not enabled for imap", "IMAP is off in Gmail"),
    ("imap access is disabled", "IMAP is off in Gmail"),
    ("log in via your web browser", "Google blocked the sign-in; confirm it at myaccount.google.com"),
    ("web login required", "Google blocked the sign-in; confirm it at myaccount.google.com"),
    ("authenticationfailed", "wrong username or password"),
    ("invalid credentials", "wrong username or password"),
)


def _reason(error: Exception) -> str:
    text = str(error).lower()
    for phrase, reason in _GMAIL_REFUSALS:
        if phrase in text:
            return reason
    if isinstance(error, socket.gaierror):
        return "mail host not found"
    if isinstance(error, TimeoutError | socket.timeout):
        return "mail host did not answer"
    if isinstance(error, ConnectionError):
        return "mail host refused the connection"
    if isinstance(error, imaplib.IMAP4.error) and ("auth" in text or "login" in text or "credentials" in text):
        return "login refused"
    if isinstance(error, imaplib.IMAP4.error):
        return "mail server refused a command"
    return type(error).__name__
