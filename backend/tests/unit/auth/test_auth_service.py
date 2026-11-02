import jwt
import pytest

from app.core.errors import Invalid, Unauthorized
from app.services.auth.providers.firebase_provider import FirebaseIdentityProvider
from tests.unit.conftest import ADMIN_EMAIL


def test_first_sign_in_creates_the_account(container):
    session = container.auth.sign_in("dev", "Anna@Example.com")
    assert session.is_new
    assert session.user.email == "anna@example.com"
    assert session.user.plan == "free"


def test_second_sign_in_reuses_the_account(container):
    first = container.auth.sign_in("dev", "anna@example.com")
    second = container.auth.sign_in("dev", "anna@example.com")
    assert not second.is_new
    assert second.user.id == first.user.id
    assert len(container.users.all()) == 1


def test_session_token_round_trip(container):
    session = container.auth.sign_in("dev", "anna@example.com")
    assert container.auth.user_from_token(session.token).id == session.user.id


def test_expired_token_is_rejected(container):
    expired = jwt.encode({"sub": "someone", "exp": 1}, container.settings.jwt_secret, algorithm="HS256")
    with pytest.raises(Unauthorized):
        container.auth.user_from_token(expired)


def test_disabled_provider_is_refused(container):
    with pytest.raises(Invalid):
        container.auth.sign_in("firebase", "token")


def test_admin_flag_comes_from_settings(container):
    assert container.auth.sign_in("dev", ADMIN_EMAIL).user.is_admin
    assert not container.auth.sign_in("dev", "someone@else.pl").user.is_admin


def test_invalid_email_is_refused(container):
    with pytest.raises(Invalid):
        container.auth.sign_in("dev", "not-an-email")


def test_firebase_provider_rejects_garbage():
    class NoKeys:
        def get_signing_key_from_jwt(self, token):
            raise jwt.PyJWTError("bad token")

    with pytest.raises(Unauthorized):
        FirebaseIdentityProvider("project", jwks_client=NoKeys()).verify("garbage")
