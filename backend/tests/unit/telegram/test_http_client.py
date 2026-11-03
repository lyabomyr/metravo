import pytest

from app.services.telegram import client as client_module
from app.services.telegram.client import HttpTelegramClient


class Reply:
    def __init__(self, status: int, body: dict | None = None):
        self.status_code, self._body, self.text = status, body or {}, str(body)

    @property
    def ok(self) -> bool:
        return self.status_code < 400

    def json(self) -> dict:
        return self._body


@pytest.fixture
def calls(monkeypatch):
    """Telegram's answers, in order; records every call so no request leaves the machine."""
    made: list[tuple[str, dict]] = []
    answers: list[Reply] = []

    def post(url, json, timeout):
        made.append((url.rsplit("/", 1)[-1], json))
        return answers.pop(0)

    monkeypatch.setattr(client_module.requests, "post", post)
    monkeypatch.setattr(client_module.time, "sleep", lambda seconds: made.append(("sleep", {"s": seconds})))
    return made, answers


def test_a_photo_is_sent_by_address(calls):
    made, answers = calls
    answers.append(Reply(200))
    assert HttpTelegramClient("t").send_photo("1", "https://img/1.jpg", "<b>500 000 zł</b>")
    assert made == [("sendPhoto", {"chat_id": "1", "photo": "https://img/1.jpg", "caption": "<b>500 000 zł</b>", "parse_mode": "HTML"})]


def test_a_photo_telegram_cannot_fetch_still_sends_the_listing(calls):
    made, answers = calls
    answers.extend([Reply(400, {"description": "wrong file identifier/HTTP URL specified"}), Reply(200)])
    assert HttpTelegramClient("t").send_photo("1", "https://img/gone.jpg", "caption")
    assert [method for method, _ in made] == ["sendPhoto", "sendMessage"]
    assert made[1][1]["text"] == "caption"


def test_too_many_messages_waits_as_told_and_retries_once(calls):
    made, answers = calls
    answers.extend([Reply(429, {"parameters": {"retry_after": 3}}), Reply(200)])
    assert HttpTelegramClient("t").send_message("1", "hi")
    assert made[1] == ("sleep", {"s": 3})
    assert [method for method, _ in made] == ["sendMessage", "sleep", "sendMessage"]


def test_a_long_wait_is_capped(calls):
    made, answers = calls
    answers.extend([Reply(429, {"parameters": {"retry_after": 600}}), Reply(429, {})])
    assert not HttpTelegramClient("t").send_message("1", "hi")
    assert ("sleep", {"s": client_module.MAX_WAIT_SECONDS}) in made


def test_a_group_that_became_a_supergroup_is_followed(calls):
    made, answers = calls
    answers.extend([Reply(400, {"parameters": {"migrate_to_chat_id": -100555}}), Reply(200)])
    client, moved = HttpTelegramClient("t"), []
    client.on_chat_moved = lambda old, new: moved.append((old, new))
    assert client.send_message("-555", "hi")
    assert moved == [("-555", "-100555")]
    assert made[1][1]["chat_id"] == "-100555"
