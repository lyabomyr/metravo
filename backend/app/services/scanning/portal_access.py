from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

from ...core.clock import Clock
from ..connectors.base import ConnectorResult

#: First pause after a refusal; it doubles on every refusal in a row, up to the cap.
FIRST_PAUSE = timedelta(minutes=30)
LONGEST_PAUSE = timedelta(hours=6)
#: Statuses that mean "you may not", not "try again in a moment".
REFUSALS = (401, 403, 451)


@dataclass
class _Portal:
    refusals: int = 0
    http_status: int | None = None
    since: datetime | None = None
    next_try: datetime | None = None
    last_ok: datetime | None = None


class PortalAccess:
    """Remembers which portals refuse us and keeps away from them for a while.

    A refusal (403 from a portal's edge) is not retried: hammering it makes a
    block worse. The portal is paused, then probed once — after 30 minutes,
    then 1 h, 2 h … up to 6 h — and resumes by itself the first time it lets
    us in. Temporary errors (429, 5xx, timeouts) are the fetcher's business:
    it retries them with backoff.
    """

    def __init__(self, clock: Clock):
        self._clock = clock
        self._portals: dict[str, _Portal] = {}
        self._lock = threading.Lock()

    def allows(self, source: str) -> bool:
        portal = self._portals.get(source)
        return portal is None or portal.next_try is None or self._clock.now() >= portal.next_try

    def paused_until(self, source: str) -> datetime | None:
        portal = self._portals.get(source)
        return portal.next_try if portal else None

    def record(self, source: str, result: ConnectorResult) -> None:
        now = self._clock.now()
        with self._lock:
            portal = self._portals.setdefault(source, _Portal())
            if result.status in REFUSALS:
                portal.refusals += 1
                portal.http_status = result.status
                portal.since = portal.since or now
                portal.next_try = now + min(FIRST_PAUSE * 2 ** (portal.refusals - 1), LONGEST_PAUSE)
            elif result.error is None:
                self._portals[source] = _Portal(last_ok=now)

    def status(self) -> dict[str, dict]:
        """Per portal: "ok", "blocked" (with since / next_try) or unknown until first fetched."""
        def iso(moment: datetime | None) -> str | None:
            return moment.isoformat(timespec="seconds") if moment else None

        return {
            source: {
                "state": "blocked" if portal.next_try else "ok",
                "http_status": portal.http_status,
                "since": iso(portal.since),
                "next_try": iso(portal.next_try),
                "last_ok": iso(portal.last_ok),
            }
            for source, portal in self._portals.items()
        }
