from app.core.errors import LimitReached
from app.core.i18n import translator
from app.core.i18n.catalogs import CATALOGS
from app.services.telegram.formatter import ListingMessageFormatter
from tests.unit.conftest import make_search


def test_every_language_has_every_key_with_the_same_placeholders():
    reference = CATALOGS["en"]
    for locale, catalog in CATALOGS.items():
        assert catalog.keys() == reference.keys(), locale
        for key, text in reference.items():
            assert set(_placeholders(catalog[key])) == set(_placeholders(text)), (locale, key)


def _placeholders(text: str) -> list[str]:
    import string

    return [name for _, name, _, _ in string.Formatter().parse(text) if name]


def test_negotiates_the_language_and_falls_back_to_english():
    assert translator.negotiate("pl-PL,pl;q=0.9,en;q=0.8") == "pl"
    assert translator.negotiate("ru") == "ru"
    assert translator.negotiate("de-DE") == "en"
    assert translator.negotiate(None) == "en"


def test_an_error_reads_in_the_requested_language():
    error = LimitReached("search.limit", plan="Free", n=1)
    assert error.message == "The Free plan allows 1 search(es)"
    assert error.text("uk") == "Тариф Free дозволяє пошуків: 1"


def test_api_errors_follow_accept_language(client):
    token = client.post("/api/auth/session", json={"provider": "dev", "credential": "ola@x.pl"}).json()["token"]
    response = client.get("/api/searches/nope", headers={"Authorization": f"Bearer {token}", "Accept-Language": "pl"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Nie znaleziono wyszukiwania", "code": "NotFound", "key": "search.not_found"}


def test_user_language_is_saved_and_used_for_listing_messages(client, container):
    token = client.post("/api/auth/session", json={"provider": "dev", "credential": "ola@x.pl"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.put("/api/auth/me/locale", json={"locale": "pl"}, headers=headers).json()["locale"] == "pl"
    assert client.put("/api/auth/me/locale", json={"locale": "xx"}, headers=headers).status_code == 422
    assert container.users.by_email("ola@x.pl").locale == "pl"

    search = make_search(name="Kraków")
    assert "nowe: 0" in ListingMessageFormatter("https://site").messages(search, [], "pl")[0]


def test_telegram_commands_answer_in_the_telegram_app_language_before_linking(container):
    reply = container.telegram_dispatcher.handle(
        {"message": {"text": "/status", "chat": {"id": 9}, "from": {"language_code": "uk"}}}
    )
    assert "ще не підключено" in reply
