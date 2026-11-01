from __future__ import annotations

from dataclasses import dataclass

from ...core.service import BaseService
from ..telegram.link_service import TelegramLinkService
from ..tenants.service import TenantService
from ..users.models import User
from ..users.service import UserService


@dataclass(frozen=True)
class Overview:
    users: int
    users_by_plan: dict[str, int]
    tenant_databases: int
    telegram_chats: int


class AdminService(BaseService):
    """Service management. Reads the control database only — never a user's own data."""

    def __init__(self, users: UserService, tenants: TenantService, telegram: TelegramLinkService):
        super().__init__()
        self._users = users
        self._tenants = tenants
        self._telegram = telegram

    def overview(self) -> Overview:
        by_plan = self._users.count_by_plan()
        return Overview(
            users=sum(by_plan.values()),
            users_by_plan=by_plan,
            tenant_databases=self._tenants.count(),
            telegram_chats=self._telegram.count_chats(),
        )

    def users(self) -> list[User]:
        return self._users.all()

    def set_plan(self, user_id: str, plan: str) -> User:
        """Manual override — comps, refunds, support cases."""
        self._users.set_plan(user_id, plan)
        return self._users.get(user_id)
