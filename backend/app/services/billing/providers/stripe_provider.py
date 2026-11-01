from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Mapping

import requests

from ....core.errors import Unauthorized
from ...users.models import User
from ..plans import Plan
from .base import BillingEvent, BillingEventKind, PaymentProvider

API = "https://api.stripe.com/v1"
#: Stripe's own recommendation for rejecting replayed webhooks.
SIGNATURE_TOLERANCE_SECONDS = 300
_CANCELLED_STATUSES = {"canceled", "unpaid", "incomplete_expired"}


class StripePaymentProvider(PaymentProvider):
    """Stripe Checkout + Customer Portal over the REST API.

    No monthly fee — Stripe only takes a cut of successful payments. Cards,
    BLIK and Przelewy24 are switched on in the Stripe dashboard, not here.
    """

    name = "stripe"

    def __init__(self, secret_key: str, webhook_secret: str, price_ids: Mapping[str, str], frontend_url: str):
        self._auth = (secret_key, "")
        self._webhook_secret = webhook_secret
        self._price_ids = price_ids
        self._frontend = frontend_url

    def create_checkout(self, user: User, plan: Plan, customer_id: str | None) -> str:
        data = {
            "mode": "subscription",
            "line_items[0][price]": self._price_ids[plan.code],
            "line_items[0][quantity]": "1",
            "client_reference_id": user.id,
            "metadata[plan]": plan.code,
            "success_url": f"{self._frontend}/billing?status=success",
            "cancel_url": f"{self._frontend}/billing?status=cancelled",
        }
        if customer_id:
            data["customer"] = customer_id
        else:
            data["customer_email"] = user.email
        return self._post("/checkout/sessions", data)["url"]

    def create_portal(self, customer_id: str) -> str:
        return self._post("/billing_portal/sessions", {"customer": customer_id, "return_url": f"{self._frontend}/billing"})["url"]

    def parse_webhook(self, payload: bytes, headers: Mapping[str, str]) -> BillingEvent | None:
        self._verify(payload, headers.get("stripe-signature", ""))
        event = json.loads(payload)
        obj = event["data"]["object"]
        if event["type"] == "checkout.session.completed":
            return BillingEvent(
                kind=BillingEventKind.ACTIVATED,
                customer_id=obj["customer"],
                user_id=obj.get("client_reference_id"),
                subscription_id=obj.get("subscription"),
                plan=(obj.get("metadata") or {}).get("plan"),
            )
        if event["type"] == "customer.subscription.deleted" or (
            event["type"] == "customer.subscription.updated" and obj.get("status") in _CANCELLED_STATUSES
        ):
            return BillingEvent(kind=BillingEventKind.CANCELLED, customer_id=obj["customer"], subscription_id=obj["id"])
        return None

    def _verify(self, payload: bytes, header: str) -> None:
        parts = dict(item.split("=", 1) for item in header.split(",") if "=" in item)
        timestamp, signature = parts.get("t", ""), parts.get("v1", "")
        expected = hmac.new(self._webhook_secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
        if not signature or not hmac.compare_digest(expected, signature):
            raise Unauthorized("Bad Stripe signature")
        if abs(time.time() - int(timestamp)) > SIGNATURE_TOLERANCE_SECONDS:
            raise Unauthorized("Stale Stripe webhook")

    def _post(self, path: str, data: dict) -> dict:
        response = requests.post(f"{API}{path}", data=data, auth=self._auth, timeout=30)
        response.raise_for_status()
        return response.json()
