from __future__ import annotations

from dataclasses import asdict

from pydantic import BaseModel

from .models import Subscription
from .plans import Plan


class PlanOut(BaseModel):
    code: str
    name: str
    price_pln: int
    max_searches: int
    scan_interval_minutes: int
    sources: list[str]
    price_alerts: bool
    database_credentials: bool

    @classmethod
    def of(cls, plan: Plan) -> PlanOut:
        return cls(**{**asdict(plan), "sources": list(plan.sources)})


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
