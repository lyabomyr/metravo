"""Every place a listing can be sent. The catalog the UI and the plans refer to."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Channel:
    code: str
    name: str
    #: What the user must give us to reach them there: "email", "phone" or None.
    address_kind: str | None


CHANNELS: tuple[Channel, ...] = (
    Channel("telegram", "Telegram", address_kind=None),
    Channel("email", "Email", address_kind="email"),
    Channel("whatsapp", "WhatsApp", address_kind="phone"),
    Channel("viber", "Viber", address_kind="phone"),
    Channel("signal", "Signal", address_kind="phone"),
)

BY_CODE = {channel.code: channel for channel in CHANNELS}
