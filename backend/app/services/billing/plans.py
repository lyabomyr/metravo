"""What each plan allows. The only place tariffs are defined."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ...core.errors import NotFound

FREE = "free"
PRO = "pro"


@dataclass(frozen=True)
class Plan:
    code: str
    name: str
    price_usd: int
    max_searches: int
    #: The most often a search on this plan may be scanned.
    min_interval_minutes: int
    sources: tuple[str, ...]
    price_alerts: bool
    #: Where listings can be sent besides the website (see notifications/channels.py).
    channels: tuple[str, ...] = ("telegram",)
    #: Before this day the plan is shown but cannot be bought. ``None`` = on sale.
    available_from: date | None = None
    #: How long the plan lasts from sign-up; ``None`` = as long as it is paid for.
    trial_days: int | None = None

    def allows_source(self, source: str) -> bool:
        return source in self.sources

    def allows_channel(self, channel: str) -> bool:
        return channel in self.channels

    def allows_interval(self, minutes: int) -> bool:
        return minutes >= self.min_interval_minutes

    def is_on_sale(self, today: date) -> bool:
        return self.available_from is None or today >= self.available_from


class PlanCatalog:
    """Look up plans by code. Iterating yields them cheapest first."""

    def __init__(self, plans: tuple[Plan, ...]):
        self._plans = {plan.code: plan for plan in plans}

    @classmethod
    def default(cls, pro_available_from: date | None = None) -> PlanCatalog:
        return cls((
            Plan(
                code=FREE,
                name="Free",
                price_usd=0,
                trial_days=7,  # a free week to see it work, then Pro
                max_searches=1,
                min_interval_minutes=1440,  # once a day
                sources=("otodom", "olx", "morizon"),
                price_alerts=False,
            ),
            Plan(
                code=PRO,
                name="Pro",
                price_usd=15,
                max_searches=5,
                min_interval_minutes=60,  # once an hour
                sources=("otodom", "olx", "morizon", "komornik"),
                price_alerts=True,
                channels=("telegram", "email", "whatsapp", "viber", "signal"),
                available_from=pro_available_from,
            ),
        ))

    def get(self, code: str) -> Plan:
        plan = self._plans.get(code)
        if plan is None:
            raise NotFound(f"Unknown plan '{code}'")
        return plan

    def __iter__(self):
        return iter(sorted(self._plans.values(), key=lambda p: p.price_usd))
