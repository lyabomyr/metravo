from app.services.system.housekeeping import Housekeeping
from tests.unit.conftest import ADMIN_EMAIL, make_search


def housekeeping(container, clock):
    return Housekeeping(container.listings, container.telegram_links, clock)


def test_offers_unseen_for_90_days_are_forgotten(container, sign_in, clock):
    user = sign_in()
    container.searches.create(user, make_search())
    container.scanner.run()
    assert container.listings.latest(user)
    clock.advance(days=89)
    housekeeping(container, clock).run_if_due()
    assert container.listings.latest(user)  # still within the window
    clock.advance(days=2)
    housekeeping(container, clock).run_if_due()
    assert container.listings.latest(user) == []
    assert container.control_db.query_one("SELECT COUNT(*) AS n FROM portal_listings")["n"] == 0


def test_offers_still_on_the_portals_stay(container, sign_in, clock):
    user = sign_in(ADMIN_EMAIL)  # never runs out, unlike the free week
    search = container.searches.create(user, make_search(interval_minutes=1440))
    for _ in range(4):  # a scan a month keeps them seen
        container.scanner.run()
        clock.advance(days=30)
    housekeeping(container, clock).run_if_due()
    assert container.listings.latest(user, search.id)


def test_old_link_tokens_are_removed(container, sign_in, clock):
    container.telegram_links.create_link(sign_in())
    clock.advance(days=2)
    fresh = container.telegram_links.create_link(sign_in("b@x.pl"))
    housekeeping(container, clock).run_if_due()
    tokens = [row["token"] for row in container.control_db.query("SELECT token FROM telegram_link_tokens")]
    assert tokens == [fresh.token]


def test_it_runs_once_a_day(container, sign_in, clock):
    tidy = housekeeping(container, clock)
    tidy.run_if_due()
    container.telegram_links.create_link(sign_in())
    clock.advance(days=2)
    tidy.run_if_due()
    clock.advance(hours=1)
    container.telegram_links.create_link(sign_in("b@x.pl"))
    clock.advance(days=1, hours=-2)  # 23 hours after the last run, the second token is old enough…
    tidy.run_if_due()  # …but it is not time yet
    assert container.control_db.query_one("SELECT COUNT(*) AS n FROM telegram_link_tokens")["n"] == 1


def test_admins_see_every_table_with_its_size(client, container, sign_in):
    container.searches.create(sign_in(), make_search())
    container.scanner.run()
    token = container.auth.sign_in("dev", ADMIN_EMAIL).token
    tables = client.get("/api/admin/database", headers={"Authorization": f"Bearer {token}"}).json()
    by_name = {table["name"]: table for table in tables}
    assert by_name["portal_listings"]["rows"] > 0 and "users" in by_name
    assert all(table["bytes"] is None or table["bytes"] > 0 for table in tables)
    assert client.get("/api/admin/database").status_code == 401
