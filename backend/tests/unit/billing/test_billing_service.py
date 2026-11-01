import json
from urllib.parse import parse_qs, urlparse

import pytest

from app.core.errors import Invalid


def complete_test_checkout(container, user, plan="pro"):
    url = container.billing.checkout_url(user, plan)
    session_id = parse_qs(urlparse(url).query)["session"][0]
    container.billing.handle_webhook(json.dumps({"type": "checkout.completed", "session_id": session_id}).encode(), {})


def test_checkout_then_webhook_upgrades_the_user(container, sign_in):
    user = sign_in()
    complete_test_checkout(container, user)
    assert container.users.get(user.id).plan == "pro"
    assert container.billing.subscription(user).status == "active"


def test_cancellation_moves_the_user_back_to_free(container, sign_in):
    user = sign_in()
    complete_test_checkout(container, user)
    customer = container.billing.subscription(user).customer_id
    container.billing.handle_webhook(json.dumps({"type": "subscription.cancelled", "customer_id": customer}).encode(), {})
    assert container.users.get(user.id).plan == "free"
    assert container.billing.subscription(user).status == "cancelled"


def test_cannot_check_out_the_free_plan_or_a_session_twice(container, sign_in):
    user = sign_in()
    with pytest.raises(Invalid):
        container.billing.checkout_url(user, "free")
    url = container.billing.checkout_url(user, "pro")
    session_id = parse_qs(urlparse(url).query)["session"][0]
    payload = json.dumps({"type": "checkout.completed", "session_id": session_id}).encode()
    container.billing.handle_webhook(payload, {})
    with pytest.raises(Invalid):
        container.billing.handle_webhook(payload, {})
