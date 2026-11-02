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
    assert {"deal_type": "rent", "property_type": "flat"} in config["source_capabilities"]["otodom"]
    assert {"deal_type": "rent", "property_type": "flat"} not in config["source_capabilities"]["komornik"]
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

    export = client.get("/api/export/listings.csv", headers=headers)
    assert export.status_code == 200
    assert export.text.startswith("search,source,title,price")
    assert 'filename="metravo-listings.csv"' in export.headers["content-disposition"]


def test_rental_search_over_http(client):
    headers = auth(client)
    body = {**SEARCH, "deal_type": "rent", "max_price": 4000, "min_area": 25}
    created = client.post("/api/searches", json=body, headers=headers).json()
    assert created["deal_type"] == "rent" and created["property_type"] == "flat"
    client.post("/api/scan/mine", headers=headers)
    listings = client.get("/api/listings", headers=headers).json()
    assert listings and {item["deal_type"] for item in listings} == {"rent"}


def test_paying_upgrades_the_plan(client):
    headers = auth(client)
    checkout_url = client.post("/api/billing/checkout", json={"plan": "pro"}, headers=headers).json()["url"]
    session_id = parse_qs(urlparse(checkout_url).query)["session"][0]
    client.post("/api/billing/webhook", content=json.dumps({"type": "checkout.completed", "session_id": session_id}))
    assert client.get("/api/auth/me", headers=headers).json()["plan"] == "pro"


def test_telegram_webhook_requires_the_secret(client):
    assert client.post("/api/telegram/webhook", json={}).status_code == 403
    ok = client.post("/api/telegram/webhook", json={}, headers={"X-Telegram-Bot-Api-Secret-Token": "dev-webhook-secret"})
    assert ok.json() == {"ok": True}


def test_admin_area_is_for_admins_only(client):
    assert client.get("/api/admin/overview", headers=auth(client)).status_code == 403
    overview = client.get("/api/admin/overview", headers=auth(client, ADMIN_EMAIL)).json()
    assert overview["users"] == 2


def test_cron_endpoint_checks_its_secret(client):
    assert client.post("/api/scan/cron").status_code == 403
    assert client.post("/api/scan/cron", headers={"X-Cron-Secret": "cron-secret"}).status_code == 202
