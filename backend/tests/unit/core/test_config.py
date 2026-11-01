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


def test_render_supplies_the_public_url_and_cors_follows_the_frontend():
    settings = Settings.from_env({"RENDER_EXTERNAL_URL": "https://api.onrender.com", "FRONTEND_URL": "https://m.pages.dev/"})
    assert settings.public_api_url == "https://api.onrender.com"
    assert settings.cors_origins == ("https://m.pages.dev",)


def test_reads_pro_launch_day_and_scheduler_switch():
    settings = Settings.from_env({"PRO_AVAILABLE_FROM": "2026-11-15", "SCHEDULER_ENABLED": "true"})
    assert str(settings.pro_available_from) == "2026-11-15"
    assert settings.scheduler_enabled


def test_production_may_run_without_payments():
    settings = Settings(env="prod", jwt_secret="x" * 32, auth_providers=("firebase",), firebase_project_id="p", billing_provider="none")
    settings.validate()
