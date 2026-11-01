from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from ...users.models import User
from ..plans import Plan


class BillingEventKind(str, Enum):
    ACTIVATED = "activated"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class BillingEvent:
    kind: BillingEventKind
    customer_id: str
    user_id: str | None = None
    subscription_id: str | None = None
    plan: str | None = None


class PaymentProvider(ABC):
    """A payment processor. Only the provider knows its API; the service only sees events."""

    name: str

    @abstractmethod
    def create_checkout(self, user: User, plan: Plan, customer_id: str | None) -> str:
        """Return the URL of a hosted payment page."""

    @abstractmethod
    def create_portal(self, customer_id: str) -> str:
        """Return the URL where the customer manages or cancels the subscription."""

    @abstractmethod
    def parse_webhook(self, payload: bytes, headers: Mapping[str, str]) -> BillingEvent | None:
        """Verify and translate a webhook call. ``None`` for events we ignore."""
