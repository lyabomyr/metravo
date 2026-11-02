"""Every place a listing can be sent. The catalog the UI and the plans refer to."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Channel:
    code: str
    name: str
    #: What the user must give us to reach them there: "email", "phone" or None.
    address_kind: str | None
    #: False while delivery is not built yet. Users can already tick it; their
    #: choice is kept and messages start flowing once a sender exists.
    live: bool


CHANNELS: tuple[Channel, ...] = (
    Channel("telegram", "Telegram", address_kind=None, live=True),
    Channel("email", "Email", address_kind="email", live=False),
    Channel("whatsapp", "WhatsApp", address_kind="phone", live=False),
    Channel("viber", "Viber", address_kind="phone", live=False),
    Channel("signal", "Signal", address_kind="phone", live=False),
)

BY_CODE = {channel.code: channel for channel in CHANNELS}
