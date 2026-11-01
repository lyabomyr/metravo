from __future__ import annotations

from dataclasses import dataclass

ACTIVE = "active"
CANCELLED = "cancelled"


@dataclass(frozen=True)
class Subscription:
    user_id: str
    provider: str
    customer_id: str
    subscription_id: str | None
    plan: str
    status: str
    updated_at: str
