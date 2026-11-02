from __future__ import annotations

from html import escape

from ...core.i18n import translator
from ..listings.models import ListingEvent
from ..notifications.senders.base import ChannelSender
from ..searches.models import Search
from ..telegram.formatter import ListingMessageFormatter
from ..users.models import User
from .mailer import Mail, Mailer


class EmailSender(ChannelSender):
    """The same listings as in Telegram, as one email per search and scan."""

    channel = "email"

    def __init__(self, mailer: Mailer, formatter: ListingMessageFormatter, website_url: str):
        self._mailer = mailer
        self._formatter = formatter
        self._website = website_url

    def deliver(self, user: User, address: str, search: Search, events: list[ListingEvent]) -> int:
        body = "<br>".join(part.replace("\n", "<br>") for part in self._formatter.messages(search, events, user.locale))
        subject = translator.t(user.locale, "email.subject", n=len(events), name=search.name)
        return int(self._mailer.send(Mail(address, subject, self._page(body, user.locale))))

    def send_test(self, user: User, address: str) -> bool:
        body = escape(translator.t(user.locale, "channel.test_message"))
        return self._mailer.send(Mail(address, translator.t(user.locale, "email.test_subject"), self._page(body, user.locale)))

    def _page(self, body: str, locale: str) -> str:
        footer = translator.t(locale, "email.footer", url=f"{self._website}/alerts")
        return (
            '<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;font-size:15px;line-height:1.5">'
            f'{body}<hr style="border:none;border-top:1px solid #ddd;margin:24px 0 12px">'
            f'<p style="color:#888;font-size:13px">{footer}</p></div>'
        )
