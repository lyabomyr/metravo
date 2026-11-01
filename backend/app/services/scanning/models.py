from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScanReport:
    searches_scanned: int = 0
    fetches: int = 0
    listings_seen: int = 0
    new_listings: int = 0
    price_changes: int = 0
    messages_sent: int = 0
    errors: list[str] = field(default_factory=list)
