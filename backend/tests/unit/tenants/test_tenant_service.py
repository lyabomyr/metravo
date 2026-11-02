import pytest
import requests

from app.core.errors import LimitReached, Unavailable
from app.services.billing.plans import PRO
from app.services.tenants.provisioners.turso_provisioner import TursoTenantProvisioner


def test_each_user_gets_a_separate_database(container, sign_in):
    anna, ben = sign_in("anna@x.pl"), sign_in("ben@x.pl")
    assert container.tenants.get(anna.id).db_url != container.tenants.get(ben.id).db_url
    container.tenants.database_for(anna.id).execute(
        "INSERT INTO searches (id, name, city, max_price, min_area, sources, reject_keywords, created_at) "
        "VALUES ('s', 'n', 'krakow', 1, 1, '[]', '[]', 'now')"
    )
    assert container.tenants.database_for(ben.id).query("SELECT * FROM searches") == []


def test_credentials_are_a_pro_feature(container, sign_in):
    user = sign_in()
    with pytest.raises(LimitReached):
        container.tenants.credentials(user, read_only=True)
    container.users.set_plan(user.id, PRO)
    credentials = container.tenants.credentials(container.users.get(user.id), read_only=True)
    assert credentials.url == container.tenants.get(user.id).db_url


class FakeResponse:
    def __init__(self, body, status_code=200):
        self.body = body
        self.status_code = status_code
        self.text = str(body)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}", response=self)

    def json(self):
        return self.body


class FakeTurso:
    """Records Platform API calls and answers like Turso does."""

    def __init__(self, create_status=200):
        self.headers = {}
        self.calls = []
        self.create_status = create_status

    def post(self, url, json=None, params=None, timeout=None):
        self.calls.append((url, json, params))
        if url.endswith("/databases"):
            if self.create_status != 200:
                return FakeResponse({"error": "turso says no"}, self.create_status)
            return FakeResponse({"database": {"Hostname": "u-1-org.turso.io"}})
        return FakeResponse({"jwt": f"jwt-{params['authorization']}"})

    def get(self, url, timeout=None):
        self.calls.append((url, None, None))
        return FakeResponse({"database": {"Hostname": "u-1-org.turso.io"}})


def test_turso_provisioner_creates_database_and_mints_scoped_tokens():
    http = FakeTurso()
    provisioner = TursoTenantProvisioner("api-token", "my-org", "default", session=http)
    created = provisioner.create("1")
    assert created.db_url == "libsql://u-1-org.turso.io"
    assert created.db_token == "jwt-full-access"
    assert http.calls[0] == ("https://api.turso.tech/v1/organizations/my-org/databases", {"name": "u-1", "group": "default"}, None)

    from app.services.tenants.models import Tenant

    tenant = Tenant("1", "turso", created.db_name, created.db_url, created.db_token, "now")
    assert provisioner.issue_credentials(tenant, read_only=True).token == "jwt-read-only"
    assert http.headers["Authorization"] == "Bearer api-token"


def test_a_database_left_from_a_failed_sign_in_is_reused():
    # Turso created the database, then the sign-in failed before we saved it.
    # Every later sign-in would hit "already exists" and fail for good.
    http = FakeTurso(create_status=409)
    created = TursoTenantProvisioner("api-token", "my-org", "default", session=http).create("1")
    assert created.db_url == "libsql://u-1-org.turso.io"
    assert http.calls[1][0] == "https://api.turso.tech/v1/organizations/my-org/databases/u-1"


def test_turso_refusing_reads_as_a_temporary_failure_not_a_crash():
    provisioner = TursoTenantProvisioner("api-token", "my-org", "default", session=FakeTurso(create_status=401))
    with pytest.raises(Unavailable) as error:
        provisioner.create("1")
    assert error.value.key == "tenant.provision_failed"
