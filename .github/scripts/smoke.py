"""After a deploy: does production work end to end? Standard library only.

    API_URL=… FRONTEND_URL=… TELEGRAM_BOT_TOKEN=… python3 .github/scripts/smoke.py

Checks the site, the API, that the browser may call the API, that private
endpoints stay private, and the Telegram bot: webhook on our API, no delivery
errors, command menu published. Prints one line per check and exits 1 if any
fails. Nothing secret is printed.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

API = os.environ["API_URL"].rstrip("/")
SITE = os.environ["FRONTEND_URL"].rstrip("/")
BOT = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TURSO_TOKEN = os.environ.get("TURSO_API_TOKEN", "")
TURSO_ORG = os.environ.get("TURSO_ORG", "")
#: Only the host: it says which Turso database is ours. The token next to it is never read.
OUR_DB_HOST = os.environ.get("CONTROL_DB_URL", "").split("://")[-1].split("/")[0]
#: Render starts the new version a few minutes after the deploy step; wait for it.
WAIT_SECONDS = int(os.environ.get("SMOKE_WAIT_SECONDS", "600"))


def request(url: str, method: str = "GET", headers: dict | None = None) -> tuple[int, dict, str]:
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "metravo-smoke", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, dict(response.headers), response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read().decode("utf-8", "replace")


def check_site() -> str:
    status, _, body = request(SITE + "/")
    assert status == 200 and "<app-root" in body, f"site answered {status}"
    status, _, body = request(SITE + "/runtime-config.json")
    assert json.loads(body)["apiUrl"].rstrip("/") == API, "the site points at another API"
    return "site is up and points at the API"


def check_api() -> str:
    assert json.loads(request(API + "/api/health")[2]) == {"status": "ok"}
    config = json.loads(request(API + "/api/config")[2])
    assert "firebase" in config["auth_providers"] and config["firebase"], "Google sign-in is not configured"
    assert {"otodom", "olx", "morizon"} <= set(config["sources"]), "portals missing"
    plans = json.loads(request(API + "/api/billing/plans")[2])
    assert [plan["code"] for plan in plans] == ["free", "pro"], "plans missing"
    portals = {name: state["state"] + (f" ({state['http_status']})" if state.get("http_status") else "")
               for name, state in config.get("portal_status", {}).items()}
    return f"API healthy; sign-in {config['auth_providers']}; portals as the server sees them: {portals or 'not checked yet'}"


def check_cors() -> str:
    _, headers, _ = request(API + "/api/auth/session", "OPTIONS", {
        "Origin": SITE, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type",
    })
    allowed = {key.lower(): value for key, value in headers.items()}.get("access-control-allow-origin")
    assert allowed == SITE, f"the browser may not call the API from {SITE} (got {allowed})"
    return "the site may call the API"


def check_private() -> str:
    for path in ("/api/auth/me", "/api/searches", "/api/places?q=krak", "/api/admin/overview"):
        status = request(API + path)[0]
        assert status == 401, f"{path} answered {status} without signing in"
    return "private endpoints need a sign-in"


def telegram(method: str) -> dict:
    return json.loads(request(f"https://api.telegram.org/bot{BOT}/{method}")[2])


def check_bot() -> str:
    me = telegram("getMe")
    assert me.get("ok"), "the bot token is not accepted"
    hook = telegram("getWebhookInfo")["result"]
    assert hook.get("url") == API + "/api/telegram/webhook", "the webhook points elsewhere"
    # An empty list means Telegram's default set, which includes channel posts.
    wanted = set(hook.get("allowed_updates") or ["message", "channel_post", "my_chat_member"])
    assert {"message", "channel_post", "my_chat_member"} <= wanted, f"the webhook skips updates: {sorted(wanted)}"
    error_at = hook.get("last_error_date") or 0
    assert time.time() - error_at > 3600, f"Telegram could not deliver recently: {hook.get('last_error_message')}"
    commands = telegram("getMyCommands")["result"]
    assert {command["command"] for command in commands} >= {"start", "status", "pause", "disconnect"}, "command menu missing"
    return f"bot @{me['result']['username']} → our webhook, {hook.get('pending_update_count', 0)} pending, {len(commands)} commands"


def megabytes(size: int) -> str:
    return f"{size / 1_000_000:.1f} MB"


def turso(path: str) -> dict:
    """GET on Turso's platform API; on a bad answer the error names the status and fields, never a value."""
    status, _, body = request(f"https://api.turso.tech/v1/organizations/{TURSO_ORG}{path}",
                              headers={"Authorization": f"Bearer {TURSO_TOKEN}"})
    data = json.loads(body) if body.strip().startswith("{") else {}
    if status != 200:
        raise LookupError(f"{path or '/'} answered HTTP {status} with fields {sorted(data)}")
    return data


def storage_of(usage: dict) -> int:
    """The usage object's storage, wherever this API version puts it."""
    for key in ("storage_bytes", "storageBytes"):
        if key in usage:
            return int(usage[key])
    nested = usage.get("usage") or usage.get("total") or {}
    return storage_of(nested) if isinstance(nested, dict) and nested else 0


def report_databases() -> None:
    """Every database in the Turso organisation and what it holds. Informational: never fails the check."""
    try:
        for database in turso("/databases")["databases"]:
            name = database.get("Name") or database.get("name")
            usage = turso(f"/databases/{name}/usage").get("database", {})
            ours = " ← Metravo" if OUR_DB_HOST and OUR_DB_HOST == (database.get("Hostname") or database.get("hostname")) else ""
            print(f"ℹ database {name}: {megabytes(storage_of(usage))} stored{ours}")
        print(f"ℹ Turso organisation total: {megabytes(storage_of(turso('/usage').get('organization', {})))} stored")
    except (KeyError, ValueError, OSError, TypeError, LookupError) as error:
        print(f"ℹ database sizes unavailable: {type(error).__name__} {error}")


def main() -> None:
    checks = [check_site, check_api, check_cors, check_private] + ([check_bot] if BOT else [])
    deadline = time.time() + WAIT_SECONDS
    failures: dict[str, str] = {}
    for check in checks:
        while True:
            try:
                print(f"✓ {check()}")
                failures.pop(check.__name__, None)
                break
            except (AssertionError, KeyError, ValueError, OSError) as error:
                failures[check.__name__] = str(error) or type(error).__name__
                if time.time() > deadline:
                    break
                time.sleep(20)  # the new version may still be starting
    if TURSO_TOKEN and TURSO_ORG:
        report_databases()
    for name, reason in failures.items():
        print(f"✗ {name}: {reason}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
