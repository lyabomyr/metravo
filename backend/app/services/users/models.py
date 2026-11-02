from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: str
    email: str
    plan: str
    created_at: str
    locale: str = "en"
    is_admin: bool = False
    #: Set by UserService when read: the end of a time-limited plan, and whether it is still running.
    free_until: str | None = None
    active: bool = True
