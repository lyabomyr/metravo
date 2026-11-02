"""Application settings, read once from the environment.

Every variable is documented in ``backend/.env.example``. ``Settings.validate``
runs at startup so a misconfigured production deploy fails immediately
instead of on the first request that needs the missing value.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date

DEV_JWT_SECRET = "dev-only-secret-change-me"


def _csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def parse_web_config(text: str) -> dict[str, str] | None:
    """Firebase's web config, as JSON or pasted straight from the console.

    The console shows JavaScript — ``const firebaseConfig = { apiKey: "…", };``
    — so accept that too: drop the assignment, quote the keys, drop trailing
    commas. Raises ``ValueError`` if it still is not an object.
    """
    text = text.strip()
    if not text:
        return None
    text = text[text.index("{"): text.rindex("}") + 1] if "{" in text and "}" in text else text
    text = re.sub(r"//[^\n]*", "", text)                                   # comments
    text = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', text)     # bare keys
    text = re.sub(r",\s*}", "}", text)                                      # trailing comma
    text = re.sub(r"'([^']*)'", r'"\1"', text)                              # single quotes
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"FIREBASE_WEB_CONFIG is not a JSON object: {error}") from None
    if not isinstance(value, dict):
        raise ValueError("FIREBASE_WEB_CONFIG is not a JSON object")
    return value


@dataclass(frozen=True)
class Settings:
    env: str = "dev"  # dev | e2e | prod

    # The one database: accounts, plans, Telegram links, and every user's searches and listings.
    control_db_url: str = "sqlite:///./data/control.db"
    control_db_token: str = ""

    # Auth
    jwt_secret: str = DEV_JWT_SECRET
    jwt_ttl_hours: int = 24 * 14
    auth_providers: tuple[str, ...] = ("dev",)
    firebase_project_id: str = ""
    firebase_web_config: str = ""  # JSON, public — handed to the frontend as-is
    admin_emails: frozenset[str] = field(default_factory=frozenset)

    # URLs
    frontend_url: str = "http://localhost:4200"
    public_api_url: str = "http://localhost:8000"
    cors_origins: tuple[str, ...] = ("http://localhost:4200",)

    # Telegram
    telegram_bot_token: str = ""
    telegram_bot_username: str = "metravo_bot"
    telegram_webhook_secret: str = "dev-webhook-secret"

    # Email alerts over SMTP. Empty host = no email channel in production.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""  # "Metravo <you@gmail.com>"; defaults to the username

    # Billing
    billing_provider: str = "fake"  # none | fake | stripe
    pro_available_from: date | None = None  # Pro is shown as "coming soon" until this day
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro: str = ""

    # Scanning
    page_fetcher: str = "http"  # http | fixtures
    fixtures_dir: str = "./tests/fixtures/pages"
    scan_pages: int = 1
    scan_delay_seconds: float = 2.0
    cron_secret: str = ""
    # The API scans by itself: every tick it runs the searches that are due.
    scheduler_enabled: bool = False
    scheduler_tick_seconds: int = 60
    # Free hosts sleep when idle; a scheduler that sleeps never fires. Pinging
    # our own public URL counts as traffic and keeps the process awake.
    keep_alive_minutes: int = 10
    # Monitoring: limits of the host when its container does not report them (0 = read from the cgroup).
    memory_limit_mb: int = 0
    cpu_cores: float = 0

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        env = os.environ if environ is None else environ
        defaults = cls()

        def get(name: str, default: str) -> str:
            return env.get(name, default)

        # Render tells every service its own public address.
        own_url = get("PUBLIC_API_URL", "") or get("RENDER_EXTERNAL_URL", "") or defaults.public_api_url
        frontend_url = get("FRONTEND_URL", defaults.frontend_url).rstrip("/")
        pro_from = get("PRO_AVAILABLE_FROM", "")

        return cls(
            env=get("APP_ENV", defaults.env),
            control_db_url=get("CONTROL_DB_URL", defaults.control_db_url),
            control_db_token=get("CONTROL_DB_TOKEN", ""),
            jwt_secret=get("JWT_SECRET", defaults.jwt_secret),
            jwt_ttl_hours=int(get("JWT_TTL_HOURS", str(defaults.jwt_ttl_hours))),
            auth_providers=_csv(get("AUTH_PROVIDERS", ",".join(defaults.auth_providers))),
            firebase_project_id=get("FIREBASE_PROJECT_ID", ""),
            firebase_web_config=get("FIREBASE_WEB_CONFIG", ""),
            admin_emails=frozenset(e.lower() for e in _csv(get("ADMIN_EMAILS", ""))),
            frontend_url=frontend_url,
            public_api_url=own_url.rstrip("/"),
            cors_origins=_csv(get("CORS_ORIGINS", frontend_url)),
            telegram_bot_token=get("TELEGRAM_BOT_TOKEN", ""),
            telegram_bot_username=get("TELEGRAM_BOT_USERNAME", defaults.telegram_bot_username),
            telegram_webhook_secret=get("TELEGRAM_WEBHOOK_SECRET", defaults.telegram_webhook_secret),
            smtp_host=get("SMTP_HOST", ""),
            smtp_port=int(get("SMTP_PORT", str(defaults.smtp_port))),
            smtp_username=get("SMTP_USERNAME", ""),
            smtp_password=get("SMTP_PASSWORD", ""),
            smtp_from=get("SMTP_FROM", ""),
            billing_provider=get("BILLING_PROVIDER", defaults.billing_provider),
            pro_available_from=date.fromisoformat(pro_from) if pro_from else None,
            stripe_secret_key=get("STRIPE_SECRET_KEY", ""),
            stripe_webhook_secret=get("STRIPE_WEBHOOK_SECRET", ""),
            stripe_price_pro=get("STRIPE_PRICE_PRO", ""),
            page_fetcher=get("PAGE_FETCHER", defaults.page_fetcher),
            fixtures_dir=get("FIXTURES_DIR", defaults.fixtures_dir),
            scan_pages=int(get("SCAN_PAGES", str(defaults.scan_pages))),
            scan_delay_seconds=float(get("SCAN_DELAY_SECONDS", str(defaults.scan_delay_seconds))),
            cron_secret=get("CRON_SECRET", ""),
            scheduler_enabled=get("SCHEDULER_ENABLED", "false").lower() in ("1", "true", "yes", "on"),
            scheduler_tick_seconds=int(get("SCHEDULER_TICK_SECONDS", str(defaults.scheduler_tick_seconds))),
            keep_alive_minutes=int(get("KEEP_ALIVE_MINUTES", str(defaults.keep_alive_minutes))),
            memory_limit_mb=int(get("MEMORY_LIMIT_MB", "0")),
            cpu_cores=float(get("CPU_CORES", "0")),
        )

    @property
    def is_production(self) -> bool:
        return self.env == "prod"

    def validate(self) -> None:
        """Crash early on settings that would only fail later, at the worst time."""
        problems: list[str] = []
        if self.is_production:
            if self.jwt_secret == DEV_JWT_SECRET:
                problems.append("JWT_SECRET must be set in production")
            if "dev" in self.auth_providers:
                problems.append("the 'dev' auth provider must not be enabled in production")
            if self.billing_provider == "fake":
                problems.append("BILLING_PROVIDER=fake is not allowed in production")
        try:
            parse_web_config(self.firebase_web_config)
        except ValueError as error:
            problems.append(str(error))
        if "firebase" in self.auth_providers and not self.firebase_project_id:
            problems.append("FIREBASE_PROJECT_ID is required for the firebase auth provider")
        if self.billing_provider == "stripe" and not (
            self.stripe_secret_key and self.stripe_webhook_secret and self.stripe_price_pro
        ):
            problems.append("STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET and STRIPE_PRICE_PRO are required")
        if problems:
            raise RuntimeError("Invalid configuration:\n  - " + "\n  - ".join(problems))
