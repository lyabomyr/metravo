from __future__ import annotations

import threading

from ...core.clock import Clock
from ...core.database import Database
from ...core.errors import LimitReached, NotFound
from ...core.repository import BaseRepository
from ...core.service import BaseService
from ..billing.plans import PlanCatalog
from ..users.models import User
from .models import DatabaseCredentials, Tenant
from .provisioners.base import TenantProvisioner
from .repository import TenantRepository


class TenantService(BaseService):
    """Every user's own database: create it, open it, hand out access to it.

    ``schema_owners`` are the repository classes whose tables live in a tenant
    database. They are injected rather than imported so this service does not
    depend on searches or listings.
    """

    def __init__(
        self,
        repo: TenantRepository,
        provisioner: TenantProvisioner,
        schema_owners: list[type[BaseRepository]],
        plans: PlanCatalog,
        clock: Clock,
    ):
        super().__init__()
        self._repo = repo
        self._provisioner = provisioner
        self._schema_owners = schema_owners
        self._plans = plans
        self._clock = clock
        self._open: dict[str, Database] = {}
        self._lock = threading.Lock()

    def ensure(self, user: User) -> Tenant:
        tenant = self._repo.by_user(user.id)
        if tenant:
            return tenant
        provisioned = self._provisioner.create(user.id)
        tenant = Tenant(
            user_id=user.id,
            provider=self._provisioner.name,
            db_name=provisioned.db_name,
            db_url=provisioned.db_url,
            db_token=provisioned.db_token,
            created_at=self._clock.iso(),
        )
        self._repo.insert(tenant)
        self.log.info("provisioned %s database for %s", tenant.provider, user.id)
        self.database_for(user.id)  # creates the tables right away
        return tenant

    def get(self, user_id: str) -> Tenant:
        return self.require(self._repo.by_user(user_id), NotFound("This account has no database yet"))

    def database_for(self, user_id: str) -> Database:
        """Open (and migrate, once per process) the user's database."""
        with self._lock:
            if user_id not in self._open:
                db = self._provisioner.open(self.get(user_id))
                for owner in self._schema_owners:
                    owner(db).migrate()
                self._open[user_id] = db
            return self._open[user_id]

    def credentials(self, user: User, read_only: bool) -> DatabaseCredentials:
        if not self._plans.get(user.plan).database_credentials:
            raise LimitReached("Direct database access is part of the Pro plan")
        return self._provisioner.issue_credentials(self.get(user.id), read_only=read_only)

    def schema(self) -> list[str]:
        return [statement for owner in self._schema_owners for statement in owner.schema()]

    def all(self) -> list[Tenant]:
        return self._repo.all()

    def count(self) -> int:
        return self._repo.count()
