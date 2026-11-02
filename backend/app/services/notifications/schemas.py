from __future__ import annotations

from pydantic import BaseModel

from .models import ChannelSetting


class ChannelOut(BaseModel):
    code: str
    name: str
    address_kind: str | None
    live: bool
    enabled: bool
    address: str
    allowed: bool

    @classmethod
    def of(cls, setting: ChannelSetting) -> ChannelOut:
        channel = setting.channel
        return cls(
            code=channel.code, name=channel.name, address_kind=channel.address_kind, live=setting.live,
            enabled=setting.enabled, address=setting.address, allowed=setting.allowed,
        )


class ChannelChange(BaseModel):
    enabled: bool
    address: str = ""
