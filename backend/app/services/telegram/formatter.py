from __future__ import annotations

from dataclasses import dataclass, replace
from html import escape

from ...core.i18n import translator
from ..connectors.models import DealType
from ..listings.models import EventKind, ListingEvent
from ..searches.models import Search

# Telegram rejects messages over 4096 characters; a rejected message is lost.
MAX_MESSAGE_LENGTH = 4000
#: More than this per scan is noise — the rest are on the website.
MAX_LISTINGS_PER_SCAN = 20
# Telegram's limit for a photo's caption; a longer card goes as text.
MAX_CAPTION_LENGTH = 1024
MAX_TITLE_LENGTH = 200


@dataclass(frozen=True)
class Card:
    """One listing as one Telegram message: its photo, when the portal has one, and a caption.

    ``photo`` is the portal's own image address. Telegram downloads it while sending,
    so we never store or fetch the picture ourselves.
    """

    text: str
    photo: str | None = None


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

    def cards(self, search: Search, events: list[ListingEvent], locale: str = "en") -> list[Card]:
        """Telegram: a card per listing, the first one under the search's header."""
        shown, hidden = events[:MAX_LISTINGS_PER_SCAN], len(events) - MAX_LISTINGS_PER_SCAN
        if not shown:
            return []
        unit = translator.t(locale, "tg.per_month") if search.deal_type is DealType.RENT else " zł"
        cards = [self._card(event, unit, locale) for event in shown]
        header = translator.t(locale, "tg.new", name=escape(search.name), n=len(events))
        cards[0] = replace(cards[0], text=f"{header}\n\n{cards[0].text}")
        # A chat may hear several searches: every card says which one it belongs to.
        cards[1:] = [replace(card, text=f"{card.text}\n🔎 <i>{escape(search.name)}</i>") for card in cards[1:]]
        if hidden > 0:
            cards.append(Card(translator.t(locale, "tg.more", n=hidden, url=f"{self._website}/listings")))
        return [card if len(card.text) <= MAX_CAPTION_LENGTH else Card(card.text) for card in cards]

    def _card(self, event: ListingEvent, unit: str, locale: str) -> Card:
        listing = event.listing
        text = self._line(event, unit, locale).removeprefix("• ")
        if listing.title:
            text = f"{text}\n{escape(listing.title[:MAX_TITLE_LENGTH])}"
        photo = listing.image_url if (listing.image_url or "").startswith(("https://", "http://")) else None
        return Card(text, photo)

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
