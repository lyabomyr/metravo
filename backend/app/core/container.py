"""The one place where objects are created and wired together.

Everything else receives its collaborators through ``__init__``. Swapping an
implementation (SQLite → Turso, Fake → Stripe) is a change here and nowhere else.
"""

from __future__ import annotations

from .clock import Clock
from .config import Settings
from .database import open_database


class Container:
    def __init__(self, settings: Settings, clock: Clock | None = None, telegram_client=None, page_fetcher=None):
        # Imports are local so ``core`` never depends on ``services`` at import time.
        from ..services.admin.service import AdminService
        from ..services.auth.providers.dev_provider import DevIdentityProvider
        from ..services.auth.providers.firebase_provider import FirebaseIdentityProvider
        from ..services.auth.service import AuthService
        from ..services.auth.tokens import SessionTokenService
        from ..services.billing.plans import PlanCatalog
        from ..services.billing.repository import SubscriptionRepository
        from ..services.billing.service import BillingService
        from ..services.connectors.registry import ConnectorRegistry
        from ..services.export.service import ExportService
        from ..services.listings.repository import ListingRepository
        from ..services.listings.service import ListingService
        from ..services.monitoring.alerts import AdminAlerter
        from ..services.monitoring.log_buffer import RecentLogs
        from ..services.monitoring.monitor import HealthMonitor
        from ..services.monitoring.probe import ResourceProbe
        from ..services.notifications.notifier import FanOutNotifier
        from ..services.notifications.repository import NotificationRepository
        from ..services.notifications.service import NotificationService
        from ..services.scanning.service import ScanService
        from ..services.searches.repository import SearchRepository
        from ..services.searches.service import SearchService
        from ..services.telegram.formatter import ListingMessageFormatter
        from ..services.telegram.link_service import TelegramLinkService
        from ..services.telegram.notifier import TelegramSender
        from ..services.telegram.repository import TelegramRepository
        from ..services.tenants.repository import TenantRepository
        from ..services.tenants.service import TenantService
        from ..services.users.repository import UserRepository
        from ..services.users.service import UserService

        self.settings = settings
        self.clock = clock or Clock()
        self.plans = PlanCatalog.default(pro_available_from=settings.pro_available_from)

        # Service-management (control) database — separate from every user's own database.
        self.control_db = open_database(settings.control_db_url, settings.control_db_token)
        user_repo = UserRepository(self.control_db)
        tenant_repo = TenantRepository(self.control_db)
        telegram_repo = TelegramRepository(self.control_db)
        subscription_repo = SubscriptionRepository(self.control_db)
        for repo in (user_repo, tenant_repo, telegram_repo, subscription_repo):
            repo.migrate()

        self.users = UserService(user_repo, self.plans, settings.admin_emails, self.clock)
        self.tenants = TenantService(
            tenant_repo,
            self._tenant_provisioner(),
            schema_owners=[SearchRepository, ListingRepository],
            plans=self.plans,
            clock=self.clock,
        )
        identity_providers = {
            "dev": lambda: DevIdentityProvider(),
            "firebase": lambda: FirebaseIdentityProvider(settings.firebase_project_id),
        }
        self.auth = AuthService(
            [identity_providers[name]() for name in settings.auth_providers],
            self.users,
            self.tenants,
            SessionTokenService(settings.jwt_secret, settings.jwt_ttl_hours, self.clock),
        )
        self.connectors = ConnectorRegistry.build(
            page_fetcher or self._page_fetcher(),
            overrides=self._fetcher_overrides() if page_fetcher is None else None,
            pages=settings.scan_pages,
            delay_seconds=settings.scan_delay_seconds,
        )
        self.searches = SearchService(self.tenants, self.users, self.connectors, self.clock)
        self.listings = ListingService(self.tenants, self.clock)
        self.export = ExportService(self.tenants)
        self.billing = BillingService(self._payment_provider(), subscription_repo, self.users, self.plans, self.clock)

        self.telegram_client = telegram_client or self._telegram_client()
        self.telegram_links = TelegramLinkService(telegram_repo, self.users, settings.telegram_bot_username, self.clock)
        self.telegram_dispatcher = self._telegram_dispatcher()

        notification_repo = NotificationRepository(self.control_db)
        notification_repo.migrate()
        self.notifications = NotificationService(notification_repo, self.users, self.clock)
        senders = [TelegramSender(self.telegram_client, self.telegram_links, ListingMessageFormatter(settings.frontend_url))]
        self.scanner = ScanService(
            self.tenants,
            self.users,
            self.searches,
            self.listings,
            self.connectors,
            FanOutNotifier(self.notifications, senders),
        )
        self.admin = AdminService(self.users, self.tenants, self.telegram_links)
        self.recent_logs = RecentLogs()
        self.monitor = HealthMonitor(
            ResourceProbe(settings.memory_limit_mb, settings.cpu_cores),
            AdminAlerter(self.users, self.telegram_links, self.telegram_client, settings.admin_emails),
        )
        self.scheduler = self._scheduler()

    # --- strategy selection ---------------------------------------------

    def _tenant_provisioner(self):
        if self.settings.tenant_provisioner == "turso":
            from ..services.tenants.provisioners.turso_provisioner import TursoTenantProvisioner

            s = self.settings
            return TursoTenantProvisioner(s.turso_api_token, s.turso_org, s.turso_group)
        from ..services.tenants.provisioners.sqlite_provisioner import SqliteTenantProvisioner

        return SqliteTenantProvisioner(self.settings.tenant_sqlite_dir)

    def _payment_provider(self):
        s = self.settings
        if s.billing_provider == "stripe":
            from ..services.billing.providers.stripe_provider import StripePaymentProvider

            return StripePaymentProvider(s.stripe_secret_key, s.stripe_webhook_secret, {"pro": s.stripe_price_pro}, s.frontend_url)
        if s.billing_provider == "none":
            from ..services.billing.providers.no_payments_provider import NoPaymentsProvider

            return NoPaymentsProvider()
        from ..services.billing.providers.fake_provider import FakePaymentProvider

        return FakePaymentProvider(s.frontend_url)

    def _scheduler(self):
        from ..services.scanning.scheduler import KeepAlive, ScanScheduler

        s = self.settings
        keep_alive = KeepAlive(f"{s.public_api_url}/api/health", s.keep_alive_minutes * 60) if s.is_production else None
        return ScanScheduler(self.scanner, s.scheduler_tick_seconds, keep_alive, self.monitor)

    def _telegram_client(self):
        from ..services.telegram.client import HttpTelegramClient, RecordingTelegramClient

        token = self.settings.telegram_bot_token
        return HttpTelegramClient(token) if token else RecordingTelegramClient()

    def _telegram_dispatcher(self):
        from ..services.telegram.commands.disconnect import DisconnectCommand
        from ..services.telegram.commands.help import HelpCommand
        from ..services.telegram.commands.pause import PauseCommand
        from ..services.telegram.commands.resume import ResumeCommand
        from ..services.telegram.commands.start import StartCommand
        from ..services.telegram.commands.status import StatusCommand
        from ..services.telegram.dispatcher import CommandDispatcher

        website = self.settings.frontend_url
        commands = [
            StartCommand(self.telegram_links, website),
            StatusCommand(self.users, self.searches, self.telegram_links),
            PauseCommand(self.telegram_links),
            ResumeCommand(self.telegram_links),
            DisconnectCommand(self.telegram_links),
        ]
        commands.append(HelpCommand(commands, website))
        return CommandDispatcher(commands, self.telegram_links, self.telegram_client, website)

    def _page_fetcher(self):
        from ..services.connectors.fetchers import FixturePageFetcher, HttpPageFetcher

        if self.settings.page_fetcher == "fixtures":
            return FixturePageFetcher(self.settings.fixtures_dir)
        return HttpPageFetcher()

    def _fetcher_overrides(self) -> dict:
        if self.settings.page_fetcher == "fixtures":
            return {}
        from ..services.connectors.fetchers import CurlTls12PageFetcher, FallbackPageFetcher, HttpPageFetcher

        # Otodom's CDN blocks one TLS fingerprint or the other depending on the day.
        return {"otodom": FallbackPageFetcher([HttpPageFetcher(), CurlTls12PageFetcher()])}
