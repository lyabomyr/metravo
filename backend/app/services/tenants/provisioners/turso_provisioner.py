from __future__ import annotations

import logging

import requests

from ....core.database import Database, TursoDatabase
from ....core.errors import Unavailable
from ..models import DatabaseCredentials, Tenant
from .base import ProvisionedDatabase, TenantProvisioner

PLATFORM_API = "https://api.turso.tech/v1"
ALREADY_EXISTS = 409

log = logging.getLogger(__name__)


class TursoTenantProvisioner(TenantProvisioner):
    """One Turso database per user, created through the Turso Platform API.

    The user gets a real, hosted libSQL database: they can connect to it with
    the Turso CLI, any libSQL SDK or plain HTTP, using credentials we mint
    for that one database only.
    """

    name = "turso"

    def __init__(self, api_token: str, organization: str, group: str, session: requests.Session | None = None):
        self._base = f"{PLATFORM_API}/organizations/{organization}"
        self._group = group
        self._http = session or requests.Session()
        self._http.headers.update({"Authorization": f"Bearer {api_token}"})

    def create(self, user_id: str) -> ProvisionedDatabase:
        name = self.db_name_for(user_id)
        try:
            response = self._http.post(f"{self._base}/databases", json={"name": name, "group": self._group}, timeout=30)
            if response.status_code == ALREADY_EXISTS:
                # Left by an earlier sign-in that failed after Turso made it.
                response = self._http.get(f"{self._base}/databases/{name}", timeout=30)
            response.raise_for_status()
            hostname = response.json()["database"]["Hostname"]
            token = self._mint_token(name, read_only=False)
        except requests.RequestException as exc:
            reply = exc.response.text[:300] if exc.response is not None else ""
            log.error("Turso could not create %s in group %s: %s %s", name, self._group, exc, reply)
            raise Unavailable("tenant.provision_failed") from exc
        return ProvisionedDatabase(db_name=name, db_url=f"libsql://{hostname}", db_token=token)

    def open(self, tenant: Tenant) -> Database:
        return TursoDatabase(tenant.db_url, tenant.db_token)

    def issue_credentials(self, tenant: Tenant, read_only: bool) -> DatabaseCredentials:
        return DatabaseCredentials(
            provider=self.name,
            url=tenant.db_url,
            token=self._mint_token(tenant.db_name, read_only=read_only),
            read_only=read_only,
            how_to_connect=f"turso db shell \"{tenant.db_url}?authToken=<token>\"  — or any libSQL client with this URL and token.",
        )

    def _mint_token(self, db_name: str, read_only: bool) -> str:
        access = "read-only" if read_only else "full-access"
        response = self._http.post(
            f"{self._base}/databases/{db_name}/auth/tokens",
            params={"authorization": access},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["jwt"]
