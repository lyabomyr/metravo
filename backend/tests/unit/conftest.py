"""Shared fixtures: a fully wired container with fake adapters and a fixed clock."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.clock import FixedClock
from app.core.config import Settings
from app.core.container import Container
from app.main import create_app
from app.services.searches.models import Search
from app.services.telegram.client import RecordingTelegramClient

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "pages"
ADMIN_EMAIL = "admin@metravo.test"


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        env="dev",
        control_db_url=f"sqlite:///{tmp_path}/control.db",
        page_fetcher="fixtures",
        fixtures_dir=str(FIXTURES),
        scan_delay_seconds=0,
        admin_emails=frozenset({ADMIN_EMAIL}),
        cron_secret="cron-secret",
    )


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 11, 1, 12, 0, tzinfo=UTC))


@pytest.fixture
def telegram() -> RecordingTelegramClient:
    return RecordingTelegramClient()


@pytest.fixture
def container(settings, clock, telegram) -> Container:
    return Container(settings, clock=clock, telegram_client=telegram)


@pytest.fixture
def client(container) -> TestClient:
    return TestClient(create_app(container=container))


@pytest.fixture
def sign_in(container):
    """``sign_in("a@b.pl")`` → the signed-in User."""

    def _sign_in(email: str = "anna@example.com"):
        return container.auth.sign_in("dev", email).user

    return _sign_in


def make_search(**overrides) -> Search:
    values = dict(
        id="",
        name="Kraków 2 pokoje",
        city="krakow",
        max_price=610000,
        min_area=39,
        sources=["otodom", "olx", "morizon"],
    )
    values.update(overrides)
    return Search(**values)
