from app.services.connectors.base import BaseConnector
from app.services.connectors.fetchers import FallbackPageFetcher, FetchError, PageFetcher
from app.services.connectors.models import Listing


class PagedFetcher(PageFetcher):
    """Serves page N as the string "N", or raises what it was told to."""

    def __init__(self, last_page: int, error_on: dict[int, FetchError] | None = None):
        self.last_page = last_page
        self.error_on = error_on or {}
        self.calls: list[str] = []

    def fetch(self, url: str) -> str:
        self.calls.append(url)
        page = int(url.split("page=")[1]) if "page=" in url else 1
        if page in self.error_on:
            raise self.error_on[page]
        if page > self.last_page:
            raise FetchError(url, 404)
        return str(page)


class TwoPerPage(BaseConnector):
    name = "fake"
    URL_TEMPLATE = "https://fake.pl/{city}"

    def parse(self, html):
        page = int(html)
        for n in (page * 2 - 1, page * 2):
            yield Listing(source=self.name, external_id=str(n), url=f"https://fake.pl/{n}", title="t")


def test_walks_pages_until_the_last_one():
    fetcher = PagedFetcher(last_page=2)
    result = TwoPerPage(fetcher, pages=5).scan("https://fake.pl/krakow")
    assert [listing.external_id for listing in result.listings] == ["1", "2", "3", "4"]
    assert result.ok


def test_a_failing_portal_reports_instead_of_raising():
    fetcher = PagedFetcher(last_page=3, error_on={1: FetchError("u", 403)})
    result = TwoPerPage(fetcher, pages=3).scan("https://fake.pl/krakow")
    assert result.listings == []
    assert "403" in result.error


def test_fallback_fetcher_tries_the_next_client():
    blocked = PagedFetcher(last_page=1, error_on={1: FetchError("u", 403)})
    working = PagedFetcher(last_page=1)
    assert FallbackPageFetcher([blocked, working]).fetch("https://fake.pl") == "1"
