import hashlib
import hmac
import json
import time

import pytest

from app.core.errors import Unauthorized
from app.services.billing.providers.base import BillingEventKind
from app.services.billing.providers.stripe_provider import StripePaymentProvider

SECRET = "whsec_test"


def provider() -> StripePaymentProvider:
    return StripePaymentProvider("sk_test", SECRET, {"pro": "price_1"}, "https://app")


def signed(event: dict, secret: str = SECRET, at: int | None = None) -> tuple[bytes, dict]:
    payload = json.dumps(event).encode()
    timestamp = str(at or int(time.time()))
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    return payload, {"stripe-signature": f"t={timestamp},v1={signature}"}


def test_checkout_completed_becomes_an_activation():
    payload, headers = signed({"type": "checkout.session.completed", "data": {"object": {
        "customer": "cus_1", "client_reference_id": "user_1", "subscription": "sub_1", "metadata": {"plan": "pro"}}}})
    event = provider().parse_webhook(payload, headers)
    assert (event.kind, event.user_id, event.customer_id, event.plan) == (BillingEventKind.ACTIVATED, "user_1", "cus_1", "pro")


def test_deleted_subscription_becomes_a_cancellation():
    payload, headers = signed({"type": "customer.subscription.deleted", "data": {"object": {"id": "sub_1", "customer": "cus_1"}}})
    assert provider().parse_webhook(payload, headers).kind is BillingEventKind.CANCELLED


def test_forged_or_replayed_webhooks_are_rejected():
    event = {"type": "checkout.session.completed", "data": {"object": {}}}
    with pytest.raises(Unauthorized):
        provider().parse_webhook(*signed(event, secret="wrong"))
    with pytest.raises(Unauthorized):
        provider().parse_webhook(*signed(event, at=int(time.time()) - 3600))


def test_unrelated_events_are_ignored():
    payload, headers = signed({"type": "invoice.paid", "data": {"object": {}}})
    assert provider().parse_webhook(payload, headers) is None
