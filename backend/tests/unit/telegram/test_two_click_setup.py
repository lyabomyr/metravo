from tests.unit.conftest import make_search


def update(text: str, chat_id: int = 777, title: str = "Anna") -> dict:
    return {"update_id": 1, "message": {"text": text, "chat": {"id": chat_id, "title": title}}}


def test_start_link_connects_the_chat(container, sign_in, telegram):
    user = sign_in()
    link = container.telegram_links.create_link(user)
    assert link.private_url == f"https://t.me/metravo_bot?start={link.token}"

    reply = container.telegram_dispatcher.handle(update(f"/start {link.token}"))

    assert "Connected to <b>anna@example.com</b>" in reply
    assert telegram.outbox[-1].chat_id == "777"
    assert [chat.chat_id for chat in container.telegram_links.chats_of(user)] == ["777"]


def test_a_link_works_only_once(container, sign_in):
    link = container.telegram_links.create_link(sign_in())
    container.telegram_dispatcher.handle(update(f"/start {link.token}"))
    reply = container.telegram_dispatcher.handle(update(f"/start {link.token}", chat_id=888))
    assert "expired" in reply or "already used" in reply


def test_a_link_expires(container, sign_in, clock):
    link = container.telegram_links.create_link(sign_in())
    clock.advance(minutes=31)
    assert "expired" in container.telegram_dispatcher.handle(update(f"/start {link.token}"))


def test_commands_need_a_connected_chat(container):
    assert "not connected" in container.telegram_dispatcher.handle(update("/status"))


def test_pause_stops_listing_messages(container, sign_in, telegram):
    user = sign_in()
    container.telegram_dispatcher.handle(update(f"/start {container.telegram_links.create_link(user).token}"))
    container.telegram_dispatcher.handle(update("/pause@metravo_bot"))
    container.searches.create(user, make_search())
    sent_before = len(telegram.outbox)
    container.scanner.run()
    assert len(telegram.outbox) == sent_before


def test_status_lists_searches(container, sign_in):
    user = sign_in()
    container.telegram_dispatcher.handle(update(f"/start {container.telegram_links.create_link(user).token}"))
    container.searches.create(user, make_search(name="Mój Kraków"))
    reply = container.telegram_dispatcher.handle(update("/status"))
    assert "Mój Kraków" in reply and "plan <b>Free</b>" in reply


def test_unknown_command_and_plain_text(container):
    assert "don't know" in container.telegram_dispatcher.handle(update("/foo"))
    assert container.telegram_dispatcher.handle(update("hello")) is None
