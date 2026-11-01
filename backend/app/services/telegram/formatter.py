from __future__ import annotations

from html import escape

from ..connectors.models import DealType
from ..listings.models import EventKind, ListingEvent
from ..searches.models import Search

# Telegram rejects messages over 4096 characters; a rejected message is lost.
MAX_MESSAGE_LENGTH = 4000
#: More than this per scan is noise — the rest are on the website.
MAX_LISTINGS_PER_SCAN = 15


class ListingMessageFormatter:
    def __init__(self, website_url: str):
        self._website = website_url

    def messages(self, search: Search, events: list[ListingEvent]) -> list[str]:
        shown, hidden = events[:MAX_LISTINGS_PER_SCAN], len(events) - MAX_LISTINGS_PER_SCAN
        header = f"🏠 <b>{escape(search.name)}</b> — {len(events)} new"
        unit = " zł/mies." if search.deal_type is DealType.RENT else " zł"
        lines = [self._line(event, unit) for event in shown]
        if hidden > 0:
            lines.append(f'…and {hidden} more on <a href="{self._website}/listings">the website</a>')
        return self._pack(header, lines)

    @staticmethod
    def _line(event: ListingEvent, unit: str) -> str:
        listing = event.listing
        price = f"{listing.price:,}{unit}".replace(",", " ") if listing.price is not None else "price n/a"
        area = f" · {listing.area:g} m²" if listing.area else ""
        place = f" · {escape(listing.location)}" if listing.location else ""
        prefix = ""
        if event.kind is EventKind.PRICE_CHANGE and event.previous_price is not None:
            arrow = "⬇️" if listing.price < event.previous_price else "⬆️"
            prefix = f"{arrow} was {event.previous_price:,} zł · ".replace(",", " ")
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
