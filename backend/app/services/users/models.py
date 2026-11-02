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
