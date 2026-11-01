from pathlib import Path

from app.services.billing.plans import PRO
from app.services.connectors.fetchers import PageFetcher
from app.services.listings.models import EventKind
from tests.unit.conftest import make_search


def link_telegram(container, user, chat_id="555"):
    link = container.telegram_links.create_link(user)
    container.telegram_links.consume(link.token, chat_id, "Anna")


def test_scan_stores_matches_and_notifies_telegram(container, sign_in, telegram):
    user = sign_in()
    link_telegram(container, user)
    container.searches.create(user, make_search())

    report = container.scanner.run()

    # otodom: 101 ✓, 102 too expensive, 103 TBS, 104 ✓ · morizon: 200 is 104's twin, 201 ✓ · olx: 301 too small, 302 ✓
    keys = {item.key for item in container.listings.latest(user)}
    assert keys == {"otodom:101", "otodom:104", "morizon:mzn201", "olx:302"}
    assert report.new_listings == 4
    assert report.searches_scanned == 1
    assert len(telegram.outbox) == 1 and "4 new" in telegram.outbox[0].text


def test_each_page_is_fetched_once_for_all_users(container, sign_in):
    for email in ("a@x.pl", "b@x.pl", "c@x.pl"):
        container.searches.create(sign_in(email), make_search())
    report = container.scanner.run()
    assert report.searches_scanned == 3
    assert report.fetches == 3  # otodom, olx, morizon — not 9


def test_search_is_not_rescanned_before_its_plan_interval(container, sign_in, clock):
    user = sign_in()
    container.searches.create(user, make_search())
    assert container.scanner.run().searches_scanned == 1
    clock.advance(minutes=30)
    assert container.scanner.run().searches_scanned == 0  # free plan: every 120 min
    clock.advance(minutes=91)
    assert container.scanner.run().searches_scanned == 1


def test_price_change_is_reported_to_pro_users(container, sign_in, telegram, clock, settings):
    user = sign_in()
    container.users.set_plan(user.id, PRO)
    link_telegram(container, user)
    search = container.searches.create(user, make_search(sources=["otodom"]))
    container.scanner.run()

    class CheaperOtodom(PageFetcher):
        def fetch(self, url):
            html = Path(settings.fixtures_dir, "otodom.pl.html").read_text(encoding="utf-8")
            return html.replace('"value": 520000', '"value": 499000')

    container.connectors.get("otodom").fetcher = CheaperOtodom()
    clock.advance(minutes=20)
    report = container.scanner.run()

    assert report.price_changes == 1
    change = container.listings.price_changes(user)[0]
    assert (change.key, change.old_price, change.new_price, change.search_id) == ("otodom:101", 520000, 499000, search.id)
    assert "was 520 000 zł" in telegram.outbox[-1].text


def test_record_returns_no_event_for_an_unchanged_listing(container, sign_in):
    user = sign_in()
    search = container.searches.create(user, make_search())
    from app.services.connectors.models import Listing

    flat = Listing(source="otodom", external_id="1", url="u", title="t", price=1, area=40.0)
    assert container.listings.record(user.id, search.id, flat).kind is EventKind.NEW
    assert container.listings.record(user.id, search.id, flat) is None
