"""Time source. Injected so tests control "now" instead of sleeping."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta


class Clock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def iso(self) -> str:
        return self.now().isoformat(timespec="seconds")


class FixedClock(Clock):
    """A clock that only moves when told to."""

    def __init__(self, at: datetime):
        self._at = at

    def now(self) -> datetime:
        return self._at

    def advance(self, **delta) -> None:
        self._at = self._at + timedelta(**delta)


def new_id() -> str:
    return uuid.uuid4().hex


def parse_iso(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
