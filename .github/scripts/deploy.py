"""Deploy helpers for .github/workflows/deploy.yml — standard library only.

GitHub Secrets are the one place settings live. This script copies them to
the hosts at deploy time and finds out the hosts' public addresses, so nobody
types a URL or a secret into Render or Cloudflare by hand.

    python3 .github/scripts/deploy.py render-url   # only find the API's URL
    python3 .github/scripts/deploy.py render       # push settings to Render, deploy → the API URL

It prints the URL and writes ``url=<…>`` to $GITHUB_OUTPUT. The website's
Cloudflare Pages project is declared in infra/terraform.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

RENDER_SERVICE = "metravo-api"

# Copied from the workflow's environment to the API on Render. Fixed settings
# (APP_ENV, BILLING_PROVIDER, …) live in render.yaml; JWT_SECRET is generated
# by Render once and never leaves it.
RENDER_SETTINGS = (
    "CONTROL_DB_URL", "CONTROL_DB_TOKEN",
    "FIREBASE_PROJECT_ID", "FIREBASE_WEB_CONFIG",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_USERNAME", "TELEGRAM_WEBHOOK_SECRET",
    "FRONTEND_URL", "ADMIN_EMAILS",
    "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM",  # email alerts
    # OLX/Otodom alert emails; empty = the SMTP mailbox over IMAP, owned by the admin
    "MAIL_ALERTS_IMAP_HOST", "MAIL_ALERTS_USERNAME", "MAIL_ALERTS_PASSWORD", "MAIL_ALERTS_OWNER",
    "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_PRO",  # once BILLING_PROVIDER=stripe
    "REMOTE_PORTALS",  # left to .github/workflows/portal-scan.yml
)


def call(method: str, url: str, token: str, body: dict | None = None) -> dict | list:
    request = urllib.request.Request(
        url,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read() or b"{}")


RENDER_API = "https://api.render.com/v1"


def render_service(token: str) -> dict:
    found = call("GET", f"{RENDER_API}/services?name={RENDER_SERVICE}&limit=1", token)
    if not found:
        sys.exit(f"No Render service named {RENDER_SERVICE}. Create it once from render.yaml (Render → New → Blueprint).")
    return found[0]["service"]


def render_url() -> str:
    return render_service(os.environ["RENDER_API_KEY"])["serviceDetails"]["url"]


def render() -> str:
    token = os.environ["RENDER_API_KEY"]
    api = RENDER_API
    service = render_service(token)
    for key in RENDER_SETTINGS:
        value = os.environ.get(key, "")
        if value:
            call("PUT", f"{api}/services/{service['id']}/env-vars/{key}", token, {"value": value})
            print(f"  set {key}", file=sys.stderr)
    call("POST", f"{api}/services/{service['id']}/deploys", token, {})
    print("Render deploy started", file=sys.stderr)
    return service["serviceDetails"]["url"]


COMMANDS = {"render-url": render_url, "render": render}


def main() -> None:
    url = COMMANDS[sys.argv[1]]().rstrip("/")
    print(url)
    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a", encoding="utf-8") as file:
            file.write(f"url={url}\n")


if __name__ == "__main__":
    main()
