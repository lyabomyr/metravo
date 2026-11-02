from __future__ import annotations

from dataclasses import dataclass

from .channels import Channel


@dataclass(frozen=True)
class ChannelSetting:
    """One channel as one user sees it: what they chose and what their plan allows."""

    channel: Channel
    enabled: bool
    address: str
    allowed: bool  # by the user's plan
