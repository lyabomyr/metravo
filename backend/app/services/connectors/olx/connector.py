"""OLX — server-rendered cards marked ``data-cy="l-card"``."""

from __future__ import annotations

import re
from collections.abc import Iterable

from bs4 import BeautifulSoup, Tag

from ..base import BaseConnector
from ..models import DealType, Listing, PropertyType, SearchQuery
from ..parsing import listing_id_from_url, parse_area, parse_price

# OLX glues the posting date onto the place: "Kraków, Nowa Huta - 04 sierpnia 2026".
# Left in, the date would leak into the address and break cross-portal matching.
_TIMESTAMP = re.compile(r"\s+-\s+(?:Odświeżono|Dzisiaj|Wczoraj|\d{1,2}\s+\w+\s+\d{4}).*$")


class OlxConnector(BaseConnector):
    name = "olx"
    FILTERS = frozenset({"market:primary", "market:secondary", "private"})
    _URL = (
        "https://www.olx.pl/nieruchomosci/{kind}/{deal}/{{city}}/"
        "?search%5Bdist%5D={{radius}}"
        "&search%5Bfilter_float_price%3Ato%5D={{max_price}}&search%5Bfilter_float_m%3Afrom%5D={{min_area}}"
    )
    RADII = (0, 2, 5, 10, 15, 30, 50, 75, 100)
    URL_TEMPLATES = {
        (DealType.SALE, PropertyType.FLAT): _URL.format(kind="mieszkania", deal="sprzedaz"),
        (DealType.RENT, PropertyType.FLAT): _URL.format(kind="mieszkania", deal="wynajem"),
        (DealType.SALE, PropertyType.HOUSE): _URL.format(kind="domy", deal="sprzedaz"),
        (DealType.RENT, PropertyType.HOUSE): _URL.format(kind="domy", deal="wynajem"),
    }

    def filter_params(self, query: SearchQuery) -> list[str]:
        # Checked in OLX's own filter form: market, private, floor_0 … floor_10. "Above 10"
        # as floor_11 follows the pattern; OLX refuses our servers, so it is unconfirmed.
        params = []
        if query.market:
            params.append(f"search%5Bfilter_enum_market%5D%5B0%5D={query.market.value}")
        if query.private_only:
            params.append("search%5Bprivate_business%5D=private")
        if floors := query.floors:
            low, high = floors
            codes = [f"floor_{n}" for n in range(low, 11) if high is None or n <= high]
            if high is None or high > 10:
                codes.append("floor_11")
            params += [f"search%5Bfilter_enum_floor_select%5D%5B{i}%5D={code}" for i, code in enumerate(codes)]
        return params

    def parse(self, html: str) -> Iterable[Listing]:
        for card in BeautifulSoup(html, "html.parser").select('[data-cy="l-card"]'):
            listing = self._to_listing(card)
            if listing:
                yield listing

    def _to_listing(self, card: Tag) -> Listing | None:
        link = card.find("a", href=True)
        if not link:
            return None
        href = link["href"]
        url = href if href.startswith("http") else f"https://www.olx.pl{href}"
        if "otodom.pl" in url:
            return None  # OLX re-lists Otodom ads; the Otodom connector owns those
        listing_id = listing_id_from_url(url) or card.get("id") or url
        title = card.find(["h4", "h6"])
        price = card.select_one('[data-testid="ad-price"]')
        place = card.select_one('[data-testid="location-date"]')
        return Listing(
            source=self.name,
            external_id=str(listing_id),
            url=url,
            title=(title or link).get_text(strip=True),
            price=parse_price(price.get_text(strip=True) if price else None),
            area=self._area(card),
            location=self._clean_location(place.get_text(strip=True) if place else None),
            image_url=self._image(card),
        )

    @staticmethod
    def _area(card: Tag) -> float | None:
        for element in card.find_all(["span", "p"]):
            text = element.get_text(strip=True)
            if "m²" in text or " m2" in text.lower():
                area = parse_area(text)
                if area is not None:
                    return area
        return None

    @staticmethod
    def _clean_location(raw: str | None) -> str | None:
        if not raw:
            return None
        return _TIMESTAMP.sub("", raw).strip() or None

    @staticmethod
    def _image(card: Tag) -> str | None:
        for img in card.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            if src.startswith("http") and not src.endswith(".svg"):
                return src
        return None
