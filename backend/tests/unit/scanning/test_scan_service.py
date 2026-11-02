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


def test_search_is_scanned_once_a_day_by_default(container, sign_in, clock):
    user = sign_in()
    container.searches.create(user, make_search())
    assert container.scanner.run().searches_scanned == 1
    clock.advance(hours=23)
    assert container.scanner.run().searches_scanned == 0
    clock.advance(hours=1)
    assert container.scanner.run().searches_scanned == 1


def test_search_follows_its_own_interval(container, sign_in, clock):
    user = sign_in()
    container.users.set_plan(user.id, PRO)
    container.searches.create(container.users.get(user.id), make_search(interval_minutes=180))
    container.scanner.run()
    clock.advance(minutes=179)
    assert container.scanner.run().searches_scanned == 0
    clock.advance(minutes=1)
    assert container.scanner.run().searches_scanned == 1


def test_plan_floor_applies_after_a_downgrade(container, sign_in, clock):
    user = sign_in()
    container.users.set_plan(user.id, PRO)
    container.searches.create(container.users.get(user.id), make_search(interval_minutes=60))
    container.scanner.run()
    container.users.set_plan(user.id, "free")
    clock.advance(minutes=60)
    assert container.scanner.run().searches_scanned == 0  # Free checks once a day
    clock.advance(hours=23)
    assert container.scanner.run().searches_scanned == 1


def test_price_change_is_reported_to_pro_users(container, sign_in, telegram, clock, settings):
    user = sign_in()
    container.users.set_plan(user.id, PRO)
    link_telegram(container, user)
    search = container.searches.create(container.users.get(user.id), make_search(sources=["otodom"], interval_minutes=60))
    container.scanner.run()

    class CheaperOtodom(PageFetcher):
        def fetch(self, url):
            html = Path(settings.fixtures_dir, "otodom.pl.html").read_text(encoding="utf-8")
            return html.replace('"value": 520000', '"value": 499000')

    container.connectors.get("otodom").fetcher = CheaperOtodom()
    clock.advance(minutes=60)
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
    assert container.listings.record(user.id, search, flat).kind is EventKind.NEW
    assert container.listings.record(user.id, search, flat) is None


def test_rental_search_reads_rental_pages_and_skips_auctions(container, sign_in, telegram):
    from app.services.billing.plans import PRO
    from app.services.connectors.models import DealType

    user = sign_in()
    container.users.set_plan(user.id, PRO)
    user = container.users.get(user.id)
    link_telegram(container, user)
    container.searches.create(user, make_search(
        name="Wynajem", deal_type=DealType.RENT, max_price=4000, min_area=25, required_keywords=["balkon"],
        sources=["otodom", "morizon"],
    ))

    report = container.scanner.run()

    # otodom: 501 ✓, 502 ✓, 503 over budget · morizon: 900 ✓
    assert {item.key for item in container.listings.latest(user)} == {"otodom:501", "otodom:502", "morizon:mzn900"}
    assert report.fetches == 2
    assert all(item.deal_type == "rent" for item in container.listings.latest(user))
    assert "2 400 zł/month" in telegram.outbox[-1].text


def test_a_search_without_limits_tracks_everything(container, sign_in):
    user = sign_in()
    container.searches.create(user, make_search(max_price=None, min_area=None, sources=["otodom", "olx"]))
    container.scanner.run()
    keys = {listing.key for listing in container.listings.latest(user)}
    assert {"otodom:102", "olx:301"} <= keys  # the 900 000 zł penthouse and the 35 m² studio
    assert "otodom:103" not in keys  # TBS is still excluded by the default "must not mention" words


def test_without_a_budget_an_unpriced_offer_is_kept(container, sign_in):
    from app.services.connectors.models import Listing
    from app.services.scanning.listing_filter import ListingFilter

    unpriced = Listing(source="otodom", external_id="9", url="https://x", title="Dom", price=None, area=120)
    assert ListingFilter(make_search(max_price=None, min_area=None)).accepts(unpriced)
    assert not ListingFilter(make_search()).accepts(unpriced)
