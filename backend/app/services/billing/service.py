from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from ...core.clock import Clock
from ...core.errors import Invalid, NotFound
from ...core.service import BaseService
from ..users.models import User
from ..users.service import UserService
from .models import ACTIVE, CANCELLED, Subscription
from .plans import FREE, Plan, PlanCatalog
from .providers.base import BillingEvent, BillingEventKind, PaymentProvider
from .repository import SubscriptionRepository


class BillingService(BaseService):
    def __init__(
        self,
        provider: PaymentProvider,
        repo: SubscriptionRepository,
        users: UserService,
        plans: PlanCatalog,
        clock: Clock,
    ):
        super().__init__()
        self._provider = provider
        self._repo = repo
        self._users = users
        self._plans = plans
        self._clock = clock

    def plans(self) -> list[Plan]:
        return list(self._plans)

    def subscription(self, user: User) -> Subscription | None:
        return self._repo.by_user(user.id)

    def checkout_url(self, user: User, plan_code: str) -> str:
        plan = self._plans.get(plan_code)
        if plan.code == FREE:
            raise Invalid("The free plan needs no checkout")
        if user.plan == plan.code:
            raise Invalid(f"You are already on {plan.name}")
        existing = self._repo.by_user(user.id)
        return self._provider.create_checkout(user, plan, existing.customer_id if existing else None)

    def portal_url(self, user: User) -> str:
        sub = self.require(self._repo.by_user(user.id), NotFound("No subscription to manage"))
        return self._provider.create_portal(sub.customer_id)

    def handle_webhook(self, payload: bytes, headers: Mapping[str, str]) -> None:
        event = self._provider.parse_webhook(payload, headers)
        if event is None:
            return
        if event.kind is BillingEventKind.ACTIVATED:
            self._activate(event)
        else:
            self._cancel(event)

    def _activate(self, event: BillingEvent) -> None:
        user_id = self.require(event.user_id, Invalid("Checkout event has no user"))
        plan = self._plans.get(event.plan or "")
        self._repo.save(Subscription(
            user_id=user_id,
            provider=self._provider.name,
            customer_id=event.customer_id,
            subscription_id=event.subscription_id,
            plan=plan.code,
            status=ACTIVE,
            updated_at=self._clock.iso(),
        ))
        self._users.set_plan(user_id, plan.code)
        self.log.info("user %s upgraded to %s", user_id, plan.code)

    def _cancel(self, event: BillingEvent) -> None:
        sub = self._repo.by_customer(event.customer_id)
        if sub is None:
            self.log.warning("cancellation for unknown customer %s", event.customer_id)
            return
        self._repo.save(replace(sub, status=CANCELLED, updated_at=self._clock.iso()))
        self._users.set_plan(sub.user_id, FREE)
        self.log.info("user %s moved back to free", sub.user_id)
