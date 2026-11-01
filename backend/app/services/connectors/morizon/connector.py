"""Morizon — server-rendered ``.card`` elements with ``data-cy`` hooks."""

from __future__ import annotations

import re
from collections.abc import Iterable

from bs4 import BeautifulSoup, Tag

from ..base import BaseConnector
from ..models import DealType, Listing, PropertyType
from ..parsing import parse_area, parse_price, parse_rooms

_ID = re.compile(r"(mzn\d+)")


class MorizonConnector(BaseConnector):
    name = "morizon"
    _QUERY = "?ps%5Bprice_to%5D={max_price}&ps%5Bliving_area_from%5D={min_area}"
    URL_TEMPLATES = {
        (DealType.SALE, PropertyType.FLAT): "https://www.morizon.pl/mieszkania/najnowsze/{city}/" + _QUERY,
        (DealType.RENT, PropertyType.FLAT): "https://www.morizon.pl/do-wynajecia/mieszkania/najnowsze/{city}/" + _QUERY,
        (DealType.SALE, PropertyType.HOUSE): "https://www.morizon.pl/domy/najnowsze/{city}/" + _QUERY,
        (DealType.RENT, PropertyType.HOUSE): "https://www.morizon.pl/do-wynajecia/domy/najnowsze/{city}/" + _QUERY,
    }

    def parse(self, html: str) -> Iterable[Listing]:
        for card in BeautifulSoup(html, "html.parser").select(".card"):
            listing = self._to_listing(card)
            if listing:
                yield listing

    def _to_listing(self, card: Tag) -> Listing | None:
        link = card.select_one('a[data-cy="propertyUrl"]') or card.find("a", href=True)
        if not link or not link.get("href"):
            return None
        href = link["href"]
        match = _ID.search(href)
        info = self._text(card, '[data-cy="propertyCardInfo"]')
        return Listing(
            source=self.name,
            external_id=match.group(1) if match else href.rsplit("/", 1)[-1],
            url=href if href.startswith("http") else f"https://www.morizon.pl{href}",
            title=self._text(card, '[data-cy="propertyCardTitle"]') or "",
            price=parse_price(self._text(card, '[data-cy="cardPropertyOfferPrice"]')),
            area=parse_area(info),
            rooms=parse_rooms(info),
            location=self._text(card, '[data-cy="propertyCardLocation"]'),
            image_url=self._image(card),
        )

    @staticmethod
    def _text(card: Tag, selector: str) -> str | None:
        element = card.select_one(selector)
        return element.get_text(" ", strip=True) if element else None

    @staticmethod
    def _image(card: Tag) -> str | None:
        # Cards also embed UI icons from /nuxt-assets/ — those are not photos.
        for img in card.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            if src.startswith("http") and not src.endswith(".svg") and "/nuxt-assets/" not in src:
                return src
        return None
