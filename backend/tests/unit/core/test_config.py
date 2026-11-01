import pytest

from app.core.config import Settings, parse_web_config


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


def test_firebase_config_may_be_pasted_from_the_console():
    pasted = """const firebaseConfig = {
      apiKey: "AIza-x",
      authDomain: 'metravo.firebaseapp.com', // comment
      projectId: "metravo",
    };"""
    assert parse_web_config(pasted) == {"apiKey": "AIza-x", "authDomain": "metravo.firebaseapp.com", "projectId": "metravo"}
    assert parse_web_config('{"apiKey": "k"}') == {"apiKey": "k"}
    assert parse_web_config("") is None


def test_unreadable_firebase_config_stops_the_start():
    with pytest.raises(RuntimeError, match="FIREBASE_WEB_CONFIG"):
        Settings(firebase_web_config="apiKey = nope").validate()
