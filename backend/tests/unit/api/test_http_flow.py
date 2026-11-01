"""The HTTP layer: auth headers, status codes and error mapping."""

import json
from urllib.parse import parse_qs, urlparse

from tests.unit.conftest import ADMIN_EMAIL

SEARCH = {"name": "Kraków", "city": "krakow", "max_price": 610000, "min_area": 39, "sources": ["otodom", "morizon"]}


def auth(client, email="anna@example.com") -> dict:
    token = client.post("/api/auth/session", json={"provider": "dev", "credential": email}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_public_endpoints(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    config = client.get("/api/config").json()
    assert config["auth_providers"] == ["dev"]
    assert "krakow" in [city["key"] for city in config["cities"]]
    assert [plan["code"] for plan in client.get("/api/billing/plans").json()] == ["free", "pro"]


def test_protected_endpoints_need_a_token(client):
    assert client.get("/api/searches").status_code == 401
    assert client.get("/api/searches", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_search_scan_listings_export(client):
    headers = auth(client)
    created = client.post("/api/searches", json=SEARCH, headers=headers)
    assert created.status_code == 201
    assert client.post("/api/searches", json=SEARCH, headers=headers).status_code == 402  # free plan limit

    assert client.post("/api/scan/mine", headers=headers).json()["new_listings"] == 3
    listings = client.get("/api/listings", headers=headers).json()
    assert {item["key"] for item in listings} == {"otodom:101", "otodom:104", "morizon:mzn201"}

    export = client.get("/api/export/database.sqlite", headers=headers)
    assert export.status_code == 200
    assert export.content.startswith(b"SQLite format 3")
    assert "attachment" in export.headers["content-disposition"]


def test_database_credentials_unlock_after_upgrade(client):
    headers = auth(client)
    assert client.post("/api/database/credentials", json={"read_only": True}, headers=headers).status_code == 402

    checkout_url = client.post("/api/billing/checkout", json={"plan": "pro"}, headers=headers).json()["url"]
    session_id = parse_qs(urlparse(checkout_url).query)["session"][0]
    client.post("/api/billing/webhook", content=json.dumps({"type": "checkout.completed", "session_id": session_id}))

    assert client.get("/api/auth/me", headers=headers).json()["plan"] == "pro"
    credentials = client.post("/api/database/credentials", json={"read_only": True}, headers=headers)
    assert credentials.status_code == 200 and credentials.json()["read_only"] is True


def test_telegram_webhook_requires_the_secret(client):
    assert client.post("/api/telegram/webhook", json={}).status_code == 403
    ok = client.post("/api/telegram/webhook", json={}, headers={"X-Telegram-Bot-Api-Secret-Token": "dev-webhook-secret"})
    assert ok.json() == {"ok": True}


def test_admin_area_is_for_admins_only(client):
    assert client.get("/api/admin/overview", headers=auth(client)).status_code == 403
    overview = client.get("/api/admin/overview", headers=auth(client, ADMIN_EMAIL)).json()
    assert overview["users"] == 2 and overview["tenant_databases"] == 2


def test_cron_endpoint_checks_its_secret(client):
    assert client.post("/api/scan/cron").status_code == 403
    assert client.post("/api/scan/cron", headers={"X-Cron-Secret": "cron-secret"}).status_code == 202
