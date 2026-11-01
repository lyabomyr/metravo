from __future__ import annotations

from ...core.repository import BaseRepository
from .models import Subscription


class SubscriptionRepository(BaseRepository):
    """Control database: one subscription record per paying (or formerly paying) user."""

    SCHEMA = (
        """CREATE TABLE IF NOT EXISTS subscriptions (
            user_id         TEXT PRIMARY KEY,
            provider        TEXT NOT NULL,
            customer_id     TEXT NOT NULL,
            subscription_id TEXT,
            plan            TEXT NOT NULL,
            status          TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )""",
        "CREATE INDEX IF NOT EXISTS subscriptions_customer ON subscriptions (customer_id)",
    )

    def by_user(self, user_id: str) -> Subscription | None:
        row = self._one("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,))
        return Subscription(**row) if row else None

    def by_customer(self, customer_id: str) -> Subscription | None:
        row = self._one("SELECT * FROM subscriptions WHERE customer_id = ?", (customer_id,))
        return Subscription(**row) if row else None

    def save(self, sub: Subscription) -> None:
        self._exec(
            """INSERT OR REPLACE INTO subscriptions
               (user_id, provider, customer_id, subscription_id, plan, status, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (sub.user_id, sub.provider, sub.customer_id, sub.subscription_id, sub.plan, sub.status, sub.updated_at),
        )
