from fastapi.testclient import TestClient

from app.main import create_app

SITE = "http://localhost:4200"


def test_a_crash_still_answers_the_site_so_it_can_say_what_happened(container, monkeypatch):
    # Without CORS headers the browser hides the response and the site can
    # only say "Cannot reach the server", which sent us looking at the network.
    def crash(*_):
        raise RuntimeError("boom")

    monkeypatch.setattr(container.auth, "sign_in", crash)
    client = TestClient(create_app(container=container), raise_server_exceptions=False)

    response = client.post(
        "/api/auth/session",
        json={"provider": "dev", "credential": "anna@example.com"},
        headers={"Origin": SITE, "Accept-Language": "uk"},
    )

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == SITE
    assert response.json()["key"] == "errors.unexpected"
    assert "boom" not in response.text
