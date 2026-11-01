from __future__ import annotations

from pydantic import BaseModel


class DatabaseInfoOut(BaseModel):
    provider: str
    db_name: str
    created_at: str
    credentials_available: bool


class CredentialsRequest(BaseModel):
    read_only: bool = True


class CredentialsOut(BaseModel):
    provider: str
    url: str
    token: str
    read_only: bool
    how_to_connect: str
