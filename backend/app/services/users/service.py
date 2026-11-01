from __future__ import annotations

from dataclasses import replace

from ...core.clock import Clock, new_id
from ...core.errors import Invalid, NotFound
from ...core.service import BaseService
from ..billing.plans import FREE, Plan, PlanCatalog
from .models import User
from .repository import UserRepository


class UserService(BaseService):
    def __init__(self, repo: UserRepository, plans: PlanCatalog, admin_emails: frozenset[str], clock: Clock):
        super().__init__()
        self._repo = repo
        self._plans = plans
        self._admin_emails = admin_emails
        self._clock = clock

    def sign_in(self, email: str) -> tuple[User, bool]:
        """Return the account for ``email``, creating it on first sign-in.

        The boolean is True for a brand-new account.
        """
        email = self._normalise(email)
        existing = self._repo.by_email(email)
        now = self._clock.iso()
        if existing:
            self._repo.touch_login(existing.id, now)
            return self._decorate(existing), False
        user_id = new_id()
        self._repo.insert(user_id, email, FREE, now)
        self.log.info("new account %s", user_id)
        return self._decorate(self._repo.by_id(user_id)), True

    def get(self, user_id: str) -> User:
        user = self.require(self._repo.by_id(user_id), NotFound("User not found"))
        return self._decorate(user)

    def plan_of(self, user: User) -> Plan:
        return self._plans.get(user.plan)

    def set_plan(self, user_id: str, plan_code: str) -> None:
        self._plans.get(plan_code)  # validates the code
        self._repo.set_plan(user_id, plan_code)

    def all(self) -> list[User]:
        return [self._decorate(user) for user in self._repo.all()]

    def count_by_plan(self) -> dict[str, int]:
        return self._repo.count_by_plan()

    def _decorate(self, user: User) -> User:
        return replace(user, is_admin=user.email in self._admin_emails)

    @staticmethod
    def _normalise(email: str) -> str:
        email = (email or "").strip().lower()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise Invalid("A valid email address is required")
        return email
