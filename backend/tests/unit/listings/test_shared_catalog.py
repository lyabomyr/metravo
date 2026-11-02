"""An offer is stored once, however many users' searches match it."""

from pathlib import Path

from app.core.database import SqliteDatabase
from app.services.billing.plans import PRO
from app.services.connectors.fetchers import PageFetcher
from app.services.listings.repository import ListingCatalog
from tests.unit.conftest import make_search
from tests.unit.scanning.test_scan_service import link_telegram


def rows(container, table: str) -> int:
    return container.control_db.query_one(f"SELECT COUNT(*) AS n FROM {table}")["n"]


def test_two_users_matching_the_same_offers_store_them_once(container, sign_in, telegram):
    anna, ben = sign_in("anna@x.pl"), sign_in("ben@x.pl")
    link_telegram(container, anna, "1")
    link_telegram(container, ben, "2")
    container.searches.create(anna, make_search())
    container.searches.create(ben, make_search())

    container.scanner.run()

    assert rows(container, "portal_listings") == 4
    assert rows(container, "search_matches") == 8
    assert {message.chat_id for message in telegram.outbox} == {"1", "2"}
    assert len(container.listings.latest(anna)) == len(container.listings.latest(ben)) == 4


def test_a_price_drop_reaches_every_user_who_had_the_offer(container, sign_in, telegram, clock, settings):
    users = [sign_in("anna@x.pl"), sign_in("ben@x.pl")]
    for chat, user in enumerate(users):
        container.users.set_plan(user.id, PRO)
        link_telegram(container, user, str(chat))
        container.searches.create(container.users.get(user.id), make_search(sources=["otodom"], interval_minutes=60))
    container.scanner.run()

    class CheaperOtodom(PageFetcher):
        def fetch(self, url):
            html = Path(settings.fixtures_dir, "otodom.pl.html").read_text(encoding="utf-8")
            return html.replace('"value": 520000', '"value": 499000')

    container.connectors.get("otodom").fetcher = CheaperOtodom()
    clock.advance(minutes=60)
    report = container.scanner.run()

    assert report.price_changes == 2  # one per user
    assert rows(container, "listing_prices") == 1  # the history is shared
    for user in users:
        assert [(c.key, c.old_price, c.new_price) for c in container.listings.price_changes(user)] == [
            ("otodom:101", 520000, 499000)
        ]


def test_rows_from_the_per_user_tables_are_moved_over(tmp_path):
    db = SqliteDatabase(str(tmp_path / "old.db"))
    db.execute(
        """CREATE TABLE listings (user_id TEXT, search_id TEXT, key TEXT, fuzzy_key TEXT, source TEXT,
           deal_type TEXT, url TEXT, title TEXT, price INTEGER, area REAL, rooms INTEGER, location TEXT,
           image_url TEXT, first_seen_at TEXT, last_seen_at TEXT, PRIMARY KEY (search_id, key))"""
    )
    db.execute(
        "CREATE TABLE price_changes (id INTEGER PRIMARY KEY, user_id TEXT, search_id TEXT, key TEXT,"
        " old_price INTEGER, new_price INTEGER, changed_at TEXT)"
    )
    for user, search in (("u1", "s1"), ("u2", "s2")):
        db.execute(
            "INSERT INTO listings VALUES (?, ?, 'otodom:1', NULL, 'otodom', 'sale', 'https://x', 'Flat', 500, 40, 2,"
            " 'Kraków', NULL, '2026-11-01T10:00:00', '2026-11-02T10:00:00')",
            (user, search),
        )
    db.execute("INSERT INTO price_changes VALUES (1, 'u1', 's1', 'otodom:1', 520, 500, '2026-11-02T09:00:00')")

    ListingCatalog.create_tables(db)

    assert db.query_one("SELECT COUNT(*) AS n FROM portal_listings")["n"] == 1
    matches = db.query("SELECT user_id, search_id, price_seen FROM search_matches ORDER BY user_id")
    assert matches == [{"user_id": "u1", "search_id": "s1", "price_seen": 500}, {"user_id": "u2", "search_id": "s2", "price_seen": 500}]
    assert db.query_one("SELECT COUNT(*) AS n FROM listing_prices")["n"] == 1
    tables = {row["name"] for row in db.query("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert "listings" not in tables and "price_changes" not in tables
