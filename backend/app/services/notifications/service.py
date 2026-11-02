from __future__ import annotations

import re

from ...core.clock import Clock
from ...core.errors import Invalid, LimitReached, NotFound
from ...core.service import BaseService
from ..users.models import User
from ..users.service import UserService
from .channels import BY_CODE, CHANNELS
from .models import ChannelSetting
from .repository import NotificationRepository

#: Enough to catch typos; whether mail arrives is what the test message is for.
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class NotificationService(BaseService):
    """Which channels a user receives listings on. Telegram is on unless switched off."""

    def __init__(self, repo: NotificationRepository, users: UserService, clock: Clock, live: frozenset[str]):
        super().__init__()
        self._repo = repo
        self._users = users
        self._clock = clock
        self._live = live

    def settings(self, user: User) -> list[ChannelSetting]:
        plan = self._users.plan_of(user)
        stored = self._repo.of(user.id)
        result = []
        for channel in CHANNELS:
            enabled, address = stored.get(channel.code, (channel.code == "telegram", ""))
            if channel.address_kind == "email" and not address:
                address = user.email
            result.append(ChannelSetting(channel, enabled, address, plan.allows_channel(channel.code), channel.code in self._live))
        return result

    def update(self, user: User, code: str, enabled: bool, address: str) -> ChannelSetting:
        channel = self.require(BY_CODE.get(code), NotFound("channel.unknown"))
        plan = self._users.plan_of(user)
        if enabled and not plan.allows_channel(code):
            raise LimitReached("channel.plan", channel=channel.name)
        address = address.strip()
        if enabled and channel.address_kind and not address:
            raise Invalid("channel.address_required", channel=channel.name)
        if enabled and channel.address_kind == "email" and not EMAIL.match(address):
            raise Invalid("channel.email_invalid")
        self._repo.save(user.id, code, enabled, address, self._clock.iso())
        return next(setting for setting in self.settings(user) if setting.channel.code == code)

    def setting(self, user: User, code: str) -> ChannelSetting:
        self.require(BY_CODE.get(code), NotFound("channel.unknown"))
        return next(setting for setting in self.settings(user) if setting.channel.code == code)

    def active(self, user: User) -> list[ChannelSetting]:
        """Channels to deliver on now: switched on and allowed by the current plan."""
        return [setting for setting in self.settings(user) if setting.enabled and setting.allowed]
