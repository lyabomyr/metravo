"""What each plan allows. The only place tariffs are defined."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.errors import NotFound

FREE = "free"
PRO = "pro"


@dataclass(frozen=True)
class Plan:
    code: str
    name: str
    price_pln: int
    max_searches: int
    scan_interval_minutes: int
    sources: tuple[str, ...]
    price_alerts: bool
    database_credentials: bool

    def allows_source(self, source: str) -> bool:
        return source in self.sources


class PlanCatalog:
    """Look up plans by code. Iterating yields them cheapest first."""

    def __init__(self, plans: tuple[Plan, ...]):
        self._plans = {plan.code: plan for plan in plans}

    @classmethod
    def default(cls) -> PlanCatalog:
        return cls((
            Plan(
                code=FREE,
                name="Free",
                price_pln=0,
                max_searches=1,
                scan_interval_minutes=120,
                sources=("otodom", "olx", "morizon"),
                price_alerts=False,
                database_credentials=False,
            ),
            Plan(
                code=PRO,
                name="Pro",
                price_pln=19,
                max_searches=5,
                scan_interval_minutes=15,
                sources=("otodom", "olx", "morizon", "komornik"),
                price_alerts=True,
                database_credentials=True,
            ),
        ))

    def get(self, code: str) -> Plan:
        plan = self._plans.get(code)
        if plan is None:
            raise NotFound(f"Unknown plan '{code}'")
        return plan

    def __iter__(self):
        return iter(sorted(self._plans.values(), key=lambda p: p.price_pln))
