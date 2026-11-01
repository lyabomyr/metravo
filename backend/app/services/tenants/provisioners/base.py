from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ....core.database import Database
from ..models import DatabaseCredentials, Tenant


@dataclass(frozen=True)
class ProvisionedDatabase:
    db_name: str
    db_url: str
    db_token: str


class TenantProvisioner(ABC):
    """Creates a database for one user and hands out access to it."""

    name: str

    @abstractmethod
    def create(self, user_id: str) -> ProvisionedDatabase:
        """Create an empty database. Must be safe to call for a new user only."""

    @abstractmethod
    def open(self, tenant: Tenant) -> Database:
        """Connect with the service's own (full-access) credentials."""

    @abstractmethod
    def issue_credentials(self, tenant: Tenant, read_only: bool) -> DatabaseCredentials:
        """Mint credentials the user can take to any client."""

    @staticmethod
    def db_name_for(user_id: str) -> str:
        # Lowercase letters, digits and dashes are valid everywhere (Turso included).
        return f"u-{user_id}"
