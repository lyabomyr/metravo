"""licytacje.komornik.pl — bailiff auctions, encoded as Nuxt "devalue" data."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable

from ..base import BaseConnector
from ..models import Listing
from ..parsing import as_int, parse_area

_NUXT_DATA = re.compile(r'<script[^>]+id="__NUXT_DATA__"[^>]*>(.+?)</script>', re.S)
_LISTING_MARKERS = frozenset({"id", "title", "openingValue", "mainCategory"})
_DETAIL_URL = "https://licytacje.komornik.pl/licytacje/{}"
# Titles also mention plot sizes ("0,2200 ha"); only flat-sized numbers count as m².
_PLAUSIBLE_FLAT_AREA = (15, 500)


class KomornikConnector(BaseConnector):
    name = "komornik"
    URL_TEMPLATE = (
        "https://licytacje.komornik.pl/wyszukiwarka-licytacji"
        "?mainCategory=REAL_ESTATE&subCategory=APARTMENTS&province={region_name}&city={city_label}"
    )

    def parse(self, html: str) -> Iterable[Listing]:
        match = _NUXT_DATA.search(html)
        if not match:
            self.log.warning("__NUXT_DATA__ not found")
            return
        for item in DevalueDecoder(json.loads(match.group(1))).objects_with(_LISTING_MARKERS):
            if item.get("mainCategory") == "REAL_ESTATE" and item.get("id") is not None:
                yield self._to_listing(item)

    def _to_listing(self, item: dict) -> Listing:
        address = item.get("address") or {}
        location = ", ".join(
            part for part in ((address.get("street") or "").strip(), (address.get("city") or "").strip(), item.get("province") or "")
            if part
        )
        estimate = item.get("estimate")
        return Listing(
            source=self.name,
            external_id=str(item["id"]),
            url=_DETAIL_URL.format(item["id"]),
            title=item.get("title") or "(no title)",
            # The starting bid is what a buyer commits to, so it is the price.
            price=as_int(item.get("openingValue")),
            area=self._area(item.get("title") or ""),
            location=location or None,
            description=f"wartość szacunkowa: {int(estimate)} zł" if estimate else None,
        )

    @staticmethod
    def _area(title: str) -> float | None:
        area = parse_area(title)
        low, high = _PLAUSIBLE_FLAT_AREA
        return area if area is not None and low <= area <= high else None


class DevalueDecoder:
    """Resolves Nuxt's flat, index-referencing payload into nested objects."""

    MAX_DEPTH = 40

    def __init__(self, data: list):
        self._data = data
        self._memo: dict[int, object] = {}

    def objects_with(self, keys: frozenset[str]) -> list[dict]:
        return [
            self._resolve(index, set(), 0)
            for index, node in enumerate(self._data)
            if isinstance(node, dict) and keys <= node.keys()
        ]

    def _resolve(self, index: int, path: set[int], depth: int):
        if depth > self.MAX_DEPTH or index in path:
            return None
        if index in self._memo:
            return self._memo[index]
        path.add(index)
        node = self._data[index]
        if isinstance(node, dict):
            value = {key: self._ref(child, path, depth) for key, child in node.items()}
        elif isinstance(node, list):
            value = [self._ref(child, path, depth) for child in node]
        else:
            value = node
        path.discard(index)
        self._memo[index] = value
        return value

    def _ref(self, child, path: set[int], depth: int):
        if isinstance(child, int) and not isinstance(child, bool) and 0 <= child < len(self._data):
            return self._resolve(child, path, depth + 1)
        return child
