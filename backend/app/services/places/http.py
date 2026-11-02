"""One polite HTTP client for the free place services: identified, throttled, cached."""

from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict

import requests

log = logging.getLogger(__name__)

USER_AGENT = "Metravo/1.0 (flat alerts; https://github.com/lyabomyr/metravo)"


class PoliteClient:
    """GETs to one free service. Returns None when it fails, so a caller can try the next service."""

    def __init__(self, base: str, min_gap_seconds: float, session: requests.Session | None = None, cache_size: int = 500):
        self._base = base
        self._gap = min_gap_seconds
        self._http = session or requests.Session()
        self._http.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "pl"})
        self._cache: OrderedDict[str, object] = OrderedDict()
        self._cache_size = cache_size
        self._lock = threading.Lock()
        self._last_call = 0.0

    @property
    def headers(self) -> dict:
        return self._http.headers

    def json(self, path: str, params: dict | list):
        return self._get(path, params, lambda response: response.json())

    def text(self, path: str, params: dict | list) -> str | None:
        return self._get(path, params, lambda response: response.text)

    def _get(self, path: str, params, read):
        key = f"{path}?{sorted(params.items()) if isinstance(params, dict) else params}"
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            time.sleep(max(0.0, self._last_call + self._gap - time.monotonic()))
            self._last_call = time.monotonic()
            try:
                response = self._http.get(self._base + path, params=params, timeout=10)
                response.raise_for_status()
                result = read(response)
            except (requests.RequestException, ValueError) as error:
                log.warning("place lookup at %s failed: %s", self._base, error)
                return None
            self._cache[key] = result
            if len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
            return result
