"""A portal that blocks us is paused and checked again later, ever less often, never hammered."""

from app.services.connectors.fetchers import FetchError, PageFetcher
from tests.unit.conftest import make_search


class Blocking(PageFetcher):
    """Answers like OLX's edge does to a data-centre address."""

    def __init__(self):
        self.calls = 0

    def fetch(self, url):
        self.calls += 1
        raise FetchError(url, 403)


def test_a_blocked_portal_is_paused_then_checked_again_with_growing_waits(container, sign_in, clock):
    olx = container.connectors.get("olx")
    real, olx.fetcher = olx.fetcher, Blocking()
    container.searches.create(sign_in(), make_search(sources=["olx"], interval_minutes=1440))

    container.scanner.run()
    assert olx.fetcher.calls == 1
    status = container.portal_access.status()["olx"]
    assert status["state"] == "blocked" and status["http_status"] == 403

    clock.advance(days=1)  # the search is due again, but the pause (30 min) has passed only once…
    container.scanner.run()
    assert olx.fetcher.calls == 2  # …so exactly one probe
    first_wait = container.portal_access.status()["olx"]["next_try"]

    clock.advance(minutes=10)
    container.scanner.run()  # not due, and paused anyway
    assert olx.fetcher.calls == 2
    assert container.portal_access.status()["olx"]["next_try"] == first_wait

    olx.fetcher = real  # the portal lets us in again
    clock.advance(days=1)
    report = container.scanner.run()
    assert container.portal_access.status()["olx"]["state"] == "ok"
    assert report.new_listings > 0


def test_paused_is_reported_not_silent(container, sign_in, clock):
    olx = container.connectors.get("olx")
    olx.fetcher = Blocking()
    user = sign_in()
    container.searches.create(user, make_search(sources=["olx"]))
    container.scanner.run()
    clock.advance(days=1)
    report = container.scanner.run()
    assert any(error.startswith("olx:") for error in report.errors)


def test_the_portals_state_is_public(client):
    assert "portal_status" in client.get("/api/config").json()


def test_at_startup_each_portal_is_checked_once(container):
    olx = container.connectors.get("olx")
    olx.fetcher = Blocking()
    container.scanner.check_portals()
    status = container.portal_access.status()
    assert olx.fetcher.calls == 1
    assert status["olx"]["state"] == "blocked" and status["otodom"]["state"] == "ok"
