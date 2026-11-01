import pytest

from app.core.errors import LimitReached
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


class FakeTurso:
    """Records Platform API calls and answers like Turso does."""

    def __init__(self):
        self.headers = {}
        self.calls = []

    def post(self, url, json=None, params=None, timeout=None):
        self.calls.append((url, json, params))
        body = {"database": {"Hostname": "u-1-org.turso.io"}} if url.endswith("/databases") else {"jwt": f"jwt-{params['authorization']}"}

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return body

        return Response()


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
