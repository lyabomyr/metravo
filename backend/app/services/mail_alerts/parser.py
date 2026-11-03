"""OLX and Otodom alert emails → listings, with what each email shows about every offer."""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup, Tag

from ..connectors.models import Listing
from ..connectors.parsing import listing_id_from_url, parse_rooms
from .inbox import AlertMail
from .redirects import RedirectResolver

#: Where an offer lives, per portal; anything else in an email (settings, help, logos) is ignored.
OFFER_ADDRESSES = {
    "olx": re.compile(r"^https?://(?:www\.|m\.)?olx\.pl/(?:d/)?oferta/[^?#\s]*-ID[A-Za-z0-9]+\.html"),
    "otodom": re.compile(r"^https?://(?:www\.)?otodom\.pl/(?:pl/)?oferta/[^?#\s]*-ID[A-Za-z0-9]+"),
}
SENDER_DOMAINS = ("olx.pl", "otodom.pl")
# A total price, not "12 500 zł/m²".
_PRICE = re.compile(r"(\d[\d\s\xa0.]*\d|\d)\s*zł(?!\s*/\s*m)", re.IGNORECASE)
_AREA = re.compile(r"(\d+(?:[.,]\d+)?)\s*m(?:²|2)(?![a-z])", re.IGNORECASE)
# Links an email has besides offers. Never followed, not even to see where they lead: one of them may unsubscribe.
_NOT_AN_OFFER = re.compile(
    r"unsubscribe|wypisz|rezygn|odsubskryb|ustawieni|settings|preferenc|powiadomie|notification|privacy|prywatno|"
    r"regulamin|pomoc|help|kontakt|contact|app\.?store|apps\.apple|play\.google|facebook|instagram|youtube|mailto:",
    re.IGNORECASE,
)
#: A card's text is short; a block longer than this holds more than one offer or the whole email.
_CARD_TEXT_LIMIT = 600


def is_offer(url: str) -> bool:
    return any(pattern.match(url) for pattern in OFFER_ADDRESSES.values())


def source_of(url: str) -> str | None:
    return next((name for name, pattern in OFFER_ADDRESSES.items() if pattern.match(url)), None)


class AlertParser:
    def __init__(self, resolver: RedirectResolver):
        self._resolver = resolver

    def listings(self, mail: AlertMail) -> list[Listing]:
        soup = BeautifulSoup(mail.html or _as_html(mail.text), "html.parser")
        offers: dict[str, Listing] = {}
        for anchor in soup.find_all("a", href=True):
            url = self._link(anchor)
            if not url:
                continue
            listing = self._read(url, _card(anchor, self._link))
            current = offers.get(listing.key)
            offers[listing.key] = _richer(current, listing) if current else listing
        return list(offers.values())

    def _link(self, anchor: Tag) -> str | None:
        """The offer a link leads to, or None — links that are plainly something else are not followed."""
        href = anchor["href"].strip()
        if not is_offer(href) and (_NOT_AN_OFFER.search(href) or _NOT_AN_OFFER.search(anchor.get_text(" ", strip=True))):
            return None
        url = href if is_offer(href) else self._resolver.resolve(href, is_offer)
        if not url:
            return None
        parts = urlsplit(url)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))  # tracking parameters dropped

    @staticmethod
    def _read(url: str, card: Tag) -> Listing:
        text = card.get_text(" ", strip=True).replace("\xa0", " ")
        prices = [int(re.sub(r"\D", "", match.group(1))) for match in _PRICE.finditer(text)]
        area = _AREA.search(text)
        return Listing(
            source=source_of(url) or "",
            external_id=listing_id_from_url(url) or url,
            url=url,
            title=_title(card, url),
            price=max(prices) if prices else None,
            area=float(area.group(1).replace(",", ".")) if area else None,
            rooms=parse_rooms(text),
            image_url=_image(card),
        )


def _card(anchor: Tag, offer_url) -> Tag:
    """The largest block around a link that is still about that one offer."""
    card, own = anchor, offer_url(anchor)
    for parent in anchor.parents:
        if parent.name in (None, "[document]", "html", "body"):
            break
        if len(parent.get_text(" ", strip=True)) > _CARD_TEXT_LIMIT:
            break
        others = {offer_url(link) for link in parent.find_all("a", href=True)} - {None, own}
        if others:
            break
        card = parent
    return card


def _title(card: Tag, url: str) -> str:
    texts = [link.get_text(" ", strip=True) for link in card.find_all("a", href=True)]
    texts += [image.get("alt", "").strip() for image in card.find_all("img")]
    words = [text for text in texts if text and not _PRICE.fullmatch(text) and len(text) > 3]
    if words:
        return max(words, key=len)[:200]
    return urlsplit(url).path.rsplit("/", 1)[-1].rsplit("-ID", 1)[0].replace("-", " ")[:200]


def _image(card: Tag) -> str | None:
    for image in card.find_all("img", src=True):
        src, width = image["src"], str(image.get("width", ""))
        if src.startswith("https://") and width not in ("0", "1"):  # tracking pixels are 1×1
            return src
    return None


def _richer(first: Listing, second: Listing) -> Listing:
    """The same offer linked twice (photo and title): keep what either link's card knew."""
    return Listing(
        source=first.source, external_id=first.external_id, url=first.url,
        title=max((first.title, second.title), key=len),
        price=first.price or second.price, area=first.area or second.area, rooms=first.rooms or second.rooms,
        image_url=first.image_url or second.image_url,
    )


def _as_html(text: str) -> str:
    """A plain-text email: every address becomes a link, so the same reading applies."""
    return re.sub(r"(https?://\S+)", r'<a href="\1">\1</a>', text)
