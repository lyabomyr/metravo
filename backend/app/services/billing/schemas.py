from __future__ import annotations

from dataclasses import asdict
from datetime import date

from pydantic import BaseModel

from .models import Subscription
from .plans import Plan


class PlanOut(BaseModel):
    code: str
    name: str
    price_pln: int
    max_searches: int
    min_interval_minutes: int
    sources: list[str]
    price_alerts: bool
    database_credentials: bool
    available_from: date | None
    on_sale: bool

    @classmethod
    def of(cls, plan: Plan, today: date) -> PlanOut:
        return cls(**{**asdict(plan), "sources": list(plan.sources), "on_sale": plan.is_on_sale(today)})


class SubscriptionOut(BaseModel):
    provider: str
    plan: str
    status: str
    updated_at: str

    @classmethod
    def of(cls, sub: Subscription) -> SubscriptionOut:
        return cls(provider=sub.provider, plan=sub.plan, status=sub.status, updated_at=sub.updated_at)


class CheckoutRequest(BaseModel):
    plan: str


class RedirectOut(BaseModel):
    url: str
