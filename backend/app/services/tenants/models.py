from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tenant:
    """A user's own database, as recorded in the control database."""

    user_id: str
    provider: str
    db_name: str
    db_url: str
    db_token: str  # full-access token the service itself uses — never sent to the browser
    created_at: str


@dataclass(frozen=True)
class DatabaseCredentials:
    """What a user needs to connect to their own database with any client."""

    provider: str
    url: str
    token: str
    read_only: bool
    how_to_connect: str
