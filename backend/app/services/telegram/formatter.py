from __future__ import annotations

from html import escape

from ...core.i18n import translator
from ..connectors.models import DealType
from ..listings.models import EventKind, ListingEvent
from ..searches.models import Search

# Telegram rejects messages over 4096 characters; a rejected message is lost.
MAX_MESSAGE_LENGTH = 4000
#: More than this per scan is noise — the rest are on the website.
MAX_LISTINGS_PER_SCAN = 15


def zloty(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


class ListingMessageFormatter:
    """Turns new listings and price changes into Telegram messages in the reader's language."""

    def __init__(self, website_url: str):
        self._website = website_url

    def messages(self, search: Search, events: list[ListingEvent], locale: str = "en") -> list[str]:
        shown, hidden = events[:MAX_LISTINGS_PER_SCAN], len(events) - MAX_LISTINGS_PER_SCAN
        header = translator.t(locale, "tg.new", name=escape(search.name), n=len(events))
        unit = translator.t(locale, "tg.per_month") if search.deal_type is DealType.RENT else " zł"
        lines = [self._line(event, unit, locale) for event in shown]
        if hidden > 0:
            lines.append(translator.t(locale, "tg.more", n=hidden, url=f"{self._website}/listings"))
        return self._pack(header, lines)

    @staticmethod
    def _line(event: ListingEvent, unit: str, locale: str) -> str:
        listing = event.listing
        price = f"{zloty(listing.price)}{unit}" if listing.price is not None else translator.t(locale, "tg.price_na")
        area = f" · {listing.area:g} m²" if listing.area else ""
        place = f" · {escape(listing.location)}" if listing.location else ""
        prefix = ""
        if event.kind is EventKind.PRICE_CHANGE and event.previous_price is not None:
            arrow = "⬇️" if listing.price < event.previous_price else "⬆️"
            prefix = f"{arrow} {translator.t(locale, 'tg.was', price=zloty(event.previous_price))} · "
        return f'• {prefix}<a href="{escape(listing.url)}">{price}{area}</a>{place} <i>[{listing.source}]</i>'

    @staticmethod
    def _pack(header: str, lines: list[str]) -> list[str]:
        messages, current = [], header
        for line in lines:
            if len(current) + len(line) + 1 > MAX_MESSAGE_LENGTH:
                messages.append(current)
                current = line
            else:
                current = f"{current}\n{line}"
        messages.append(current)
        return messages
