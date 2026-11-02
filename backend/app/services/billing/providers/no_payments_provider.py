from __future__ import annotations

from collections.abc import Mapping

from ....core.errors import Invalid
from ...users.models import User
from ..plans import Plan
from .base import BillingEvent, PaymentProvider


class NoPaymentsProvider(PaymentProvider):
    """Before payments open: everyone is on Free and nothing can be bought.

    Swap for ``stripe`` with ``BILLING_PROVIDER`` when the paid plan launches;
    no other code changes.
    """

    name = "none"

    def create_checkout(self, user: User, plan: Plan, customer_id: str | None) -> str:
        raise Invalid("billing.not_open")

    def create_portal(self, customer_id: str) -> str:
        raise Invalid("billing.not_open")

    def parse_webhook(self, payload: bytes, headers: Mapping[str, str]) -> BillingEvent | None:
        return None
