import pytest

from app.core.config import Settings


def test_defaults_are_valid_for_development():
    Settings().validate()


def test_production_refuses_development_shortcuts():
    with pytest.raises(RuntimeError) as error:
        Settings(env="prod").validate()
    message = str(error.value)
    assert "JWT_SECRET" in message
    assert "'dev' auth provider" in message
    assert "BILLING_PROVIDER=fake" in message


def test_reads_environment():
    settings = Settings.from_env({"APP_ENV": "e2e", "ADMIN_EMAILS": "A@x.pl, b@y.pl", "AUTH_PROVIDERS": "dev,firebase"})
    assert settings.env == "e2e"
    assert settings.admin_emails == frozenset({"a@x.pl", "b@y.pl"})
    assert settings.auth_providers == ("dev", "firebase")
