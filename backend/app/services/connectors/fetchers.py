"""How connectors get HTML. Swappable so tests never touch the network."""

from __future__ import annotations

import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


class FetchError(RuntimeError):
    def __init__(self, url: str, status: int | None, message: str = ""):
        super().__init__(message or f"HTTP {status} for {url}")
        self.url = url
        self.status = status


class PageFetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> str:
        """Return the page body or raise ``FetchError``."""


class HttpPageFetcher(PageFetcher):
    """``requests`` with retries on transient errors only.

    403 is deliberately not retried: on these portals it means a bot shield,
    and hammering it makes the block worse.
    """

    def __init__(self, timeout: int = 30):
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "pl,en;q=0.8"})
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retry))

    def fetch(self, url: str) -> str:
        try:
            response = self._session.get(url, timeout=self._timeout)
        except requests.RequestException as exc:
            raise FetchError(url, None, str(exc)) from exc
        if response.status_code != 200:
            raise FetchError(url, response.status_code)
        return response.text


class CurlTls12PageFetcher(PageFetcher):
    """curl pinned to TLS 1.2.

    Otodom's CloudFront fingerprints the TLS handshake; at times it blocks
    ``requests`` and lets curl-with-TLS-1.2 through, at times the reverse.
    """

    _STATUS_MARKER = "\n__HTTP_STATUS__:"

    def __init__(self, timeout: int = 30):
        self._timeout = timeout

    def fetch(self, url: str) -> str:
        curl = shutil.which("curl")
        if not curl:
            raise FetchError(url, None, "curl is not installed")
        result = subprocess.run(
            [curl, "--silent", "--location", "--compressed", "--tlsv1.2", "--tls-max", "1.2",
             "--write-out", self._STATUS_MARKER + "%{http_code}", "--max-time", str(self._timeout),
             "-A", USER_AGENT, "-H", "Accept-Language: pl,en;q=0.8", url],
            capture_output=True, text=True, check=False,
        )
        body, _, status = result.stdout.rpartition(self._STATUS_MARKER)
        code = int(status) if status.strip().isdigit() else None
        if code != 200:
            raise FetchError(url, code)
        return body


class FallbackPageFetcher(PageFetcher):
    """Try each fetcher in turn; the first page wins."""

    def __init__(self, fetchers: list[PageFetcher]):
        self._fetchers = fetchers

    def fetch(self, url: str) -> str:
        error: FetchError | None = None
        for fetcher in self._fetchers:
            try:
                return fetcher.fetch(url)
            except FetchError as exc:
                error = exc
                if exc.status in (404, 410):
                    break  # the page really does not exist — no point retrying elsewhere
        raise error or FetchError(url, None, "no fetcher configured")


class FixturePageFetcher(PageFetcher):
    """Serves saved pages from disk: ``<dir>/<portal-host>[.rent].html``.

    Used by unit and e2e tests so scans are deterministic and offline. Rental
    searches get the ``.rent`` page. Any page after the first is reported as
    missing, which ends the walk.
    """

    #: URL fragments the portals use for rentals.
    RENT_MARKERS = ("wynajem", "do-wynajecia")

    def __init__(self, directory: str):
        self._directory = Path(directory)

    def fetch(self, url: str) -> str:
        if "page=" in url:
            raise FetchError(url, 404)
        host = (urlparse(url).hostname or "").removeprefix("www.")
        variant = ".rent" if any(marker in url for marker in self.RENT_MARKERS) else ""
        path = self._directory / f"{host}{variant}.html"
        if not path.exists():
            raise FetchError(url, 404, f"no fixture at {path}")
        return path.read_text(encoding="utf-8")
