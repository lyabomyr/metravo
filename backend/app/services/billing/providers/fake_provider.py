from __future__ import annotations

import json
import secrets
from collections.abc import Mapping

from ....core.errors import Invalid
from ...users.models import User
from ..plans import Plan
from .base import BillingEvent, BillingEventKind, PaymentProvider


class FakePaymentProvider(PaymentProvider):
    """Behaves like Stripe without money or an account.

    Checkout and portal URLs point at test pages in the frontend; those pages
    call our own webhook with the same kind of event Stripe would send. That
    keeps the whole billing flow — redirect, webhook, plan change — testable
    end to end. ``Settings.validate`` forbids it in production.
    """

    name = "fake"

    def __init__(self, frontend_url: str):
        self._frontend = frontend_url
        self._sessions: dict[str, tuple[str, str]] = {}

    def create_checkout(self, user: User, plan: Plan, customer_id: str | None) -> str:
        session_id = secrets.token_urlsafe(12)
        self._sessions[session_id] = (user.id, plan.code)
        return f"{self._frontend}/billing/test-checkout?session={session_id}&plan={plan.code}"

    def create_portal(self, customer_id: str) -> str:
        return f"{self._frontend}/billing/test-portal?customer={customer_id}"

    def parse_webhook(self, payload: bytes, headers: Mapping[str, str]) -> BillingEvent | None:
        body = json.loads(payload or b"{}")
        if body.get("type") == "checkout.completed":
            if body.get("session_id") not in self._sessions:
                raise Invalid("Unknown test checkout session")
            user_id, plan = self._sessions.pop(body["session_id"])
            return BillingEvent(
                kind=BillingEventKind.ACTIVATED,
                customer_id=f"cus_test_{user_id}",
                user_id=user_id,
                subscription_id=f"sub_test_{user_id}",
                plan=plan,
            )
        if body.get("type") == "subscription.cancelled":
            return BillingEvent(kind=BillingEventKind.CANCELLED, customer_id=body["customer_id"])
        return None
