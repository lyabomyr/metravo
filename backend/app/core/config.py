"""Application settings, read once from the environment.

Every variable is documented in ``backend/.env.example``. ``Settings.validate``
runs at startup so a misconfigured production deploy fails immediately
instead of on the first request that needs the missing value.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date

DEV_JWT_SECRET = "dev-only-secret-change-me"


def _csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


@dataclass(frozen=True)
class Settings:
    env: str = "dev"  # dev | e2e | prod

    # Service-management database: users, tenants, subscriptions, telegram links.
    control_db_url: str = "sqlite:///./data/control.db"
    control_db_token: str = ""

    # Where each user's own database lives.
    tenant_provisioner: str = "sqlite"  # sqlite | turso
    tenant_sqlite_dir: str = "./data/tenants"
    turso_api_token: str = ""
    turso_org: str = ""
    turso_group: str = "default"

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
            tenant_provisioner=get("TENANT_PROVISIONER", defaults.tenant_provisioner),
            tenant_sqlite_dir=get("TENANT_SQLITE_DIR", defaults.tenant_sqlite_dir),
            turso_api_token=get("TURSO_API_TOKEN", ""),
            turso_org=get("TURSO_ORG", ""),
            turso_group=get("TURSO_GROUP", defaults.turso_group),
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
        if "firebase" in self.auth_providers and not self.firebase_project_id:
            problems.append("FIREBASE_PROJECT_ID is required for the firebase auth provider")
        if self.tenant_provisioner == "turso" and not (self.turso_api_token and self.turso_org):
            problems.append("TURSO_API_TOKEN and TURSO_ORG are required for TENANT_PROVISIONER=turso")
        if self.billing_provider == "stripe" and not (
            self.stripe_secret_key and self.stripe_webhook_secret and self.stripe_price_pro
        ):
            problems.append("STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET and STRIPE_PRICE_PRO are required")
        if problems:
            raise RuntimeError("Invalid configuration:\n  - " + "\n  - ".join(problems))
