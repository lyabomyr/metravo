"""Otodom — reads the structured ``__NEXT_DATA__`` JSON, not the HTML cards."""

from __future__ import annotations

import json
from collections.abc import Iterable

from bs4 import BeautifulSoup

from ..base import BaseConnector
from ..models import Listing
from ..parsing import as_float, as_int

# Otodom has moved the result list around between releases; try each known home.
_ITEM_PATHS = (
    ("props", "pageProps", "data", "searchAds", "items"),
    ("props", "pageProps", "data", "listing", "items"),
    ("props", "pageProps", "searchAds", "items"),
)


class OtodomConnector(BaseConnector):
    name = "otodom"
    URL_TEMPLATE = (
        "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/{region_slug}/{city}/{city}/{city}"
        "?priceMax={max_price}&areaMin={min_area}&limit=36&by=LATEST&direction=DESC"
    )

    def parse(self, html: str) -> Iterable[Listing]:
        tag = BeautifulSoup(html, "html.parser").find("script", id="__NEXT_DATA__")
        if not tag or not tag.string:
            self.log.warning("__NEXT_DATA__ not found")
            return
        for item in self._items(json.loads(tag.string)):
            listing = self._to_listing(item)
            if listing:
                yield listing

    @staticmethod
    def _items(data: dict) -> list:
        for path in _ITEM_PATHS:
            node = data
            for key in path:
                node = node.get(key) if isinstance(node, dict) else None
            if isinstance(node, list):
                return node
        return []

    def _to_listing(self, item: dict) -> Listing | None:
        listing_id, slug = item.get("id"), item.get("slug")
        if not listing_id or not slug:
            return None
        return Listing(
            source=self.name,
            external_id=str(listing_id),
            url=f"https://www.otodom.pl/pl/oferta/{slug}",
            title=item.get("title") or "",
            price=as_int(self._price(item)),
            area=as_float(self._number(item, "areaInSquareMeters", "area")),
            rooms=as_int(self._number(item, "roomsNumber", "rooms")),
            location=self._location(item),
            build_year=as_int(self._number(item, "buildYear", "yearBuilt")),
            description=item.get("shortDescription") or item.get("description"),
            image_url=self._image(item),
        )

    @staticmethod
    def _price(item: dict):
        total = item.get("totalPrice")
        if isinstance(total, dict) and total.get("value") is not None:
            return total["value"]
        return item.get("price")

    @staticmethod
    def _number(item: dict, *keys: str):
        for key in keys:
            value = item.get(key)
            if isinstance(value, (int, float)):
                return value
            if isinstance(value, dict) and "value" in value:
                return value["value"]
        return None

    @staticmethod
    def _location(item: dict) -> str | None:
        address = (item.get("location") or {}).get("address") or {}
        parts = [
            address[key]["name"]
            for key in ("street", "district", "city")
            if isinstance(address.get(key), dict) and address[key].get("name")
        ]
        if parts:
            return ", ".join(parts)
        geo = ((item.get("location") or {}).get("reverseGeocoding") or {}).get("locations") or []
        names = [level.get("fullName") for level in geo if isinstance(level, dict) and level.get("fullName")]
        return names[0] if names else None

    @staticmethod
    def _image(item: dict) -> str | None:
        images = item.get("images")
        if not isinstance(images, list) or not images:
            return None
        first = images[0]
        if isinstance(first, dict):
            return first.get("medium") or first.get("large") or first.get("small")
        return first if isinstance(first, str) else None
