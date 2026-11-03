"""Alert emails wrap offer links in click trackers. This finds the offer address behind them."""

from __future__ import annotations

import logging
from collections.abc import Callable
from urllib.parse import parse_qsl, unquote, urljoin, urlsplit

import requests

log = logging.getLogger(__name__)

_REDIRECTS = (301, 302, 303, 307, 308)


class RedirectResolver:
    """Follows a tracker's ``Location`` headers until an offer address appears.

    The offer page itself is never requested: the walk stops as soon as the
    next address is one. An address embedded in the link (``?url=…``) needs no
    request at all.
    """

    def __init__(self, http: requests.Session | None = None, hops: int = 4, timeout: int = 10):
        self._http = http or requests.Session()
        self._hops = hops
        self._timeout = timeout
        self._cache: dict[str, str | None] = {}

    def resolve(self, url: str, is_offer: Callable[[str], bool]) -> str | None:
        if url not in self._cache:
            self._cache[url] = self._walk(url, is_offer)
        return self._cache[url]

    def _walk(self, url: str, is_offer: Callable[[str], bool]) -> str | None:
        for _ in range(self._hops):
            if is_offer(url):
                return url
            if embedded := _embedded(url, is_offer):
                return embedded
            if not url.startswith(("https://", "http://")):
                return None
            try:
                response = self._http.head(url, allow_redirects=False, timeout=self._timeout)
                if response.status_code in (403, 405):  # some trackers only answer GET
                    response = self._http.get(url, allow_redirects=False, timeout=self._timeout, stream=True)
                    response.close()
            except requests.RequestException as error:
                log.info("could not follow %s: %s", urlsplit(url).netloc, error)
                return None
            location = response.headers.get("Location")
            if response.status_code not in _REDIRECTS or not location:
                return None
            url = urljoin(url, location)
        return url if is_offer(url) else None


def _embedded(url: str, is_offer: Callable[[str], bool]) -> str | None:
    for _, value in parse_qsl(urlsplit(url).query):
        candidate = unquote(value)
        if is_offer(candidate):
            return candidate
    return None
