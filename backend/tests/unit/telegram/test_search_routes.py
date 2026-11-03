from app.services.connectors.models import DealType
from tests.unit.conftest import make_search
from tests.unit.telegram.test_two_click_setup import update


def connect(container, user, chat_id, search_id=None, title="chat"):
    token = container.telegram_links.create_link(user, search_id).token
    container.telegram_dispatcher.handle(update(f"/start {token}", chat_id=chat_id, title=title))


def listing_chats(telegram):
    return {message.chat_id for message in telegram.outbox if "zł" in message.text}


def test_a_group_connected_from_a_search_hears_only_that_search(container, sign_in, telegram, clock):
    user = sign_in("admin@metravo.test")  # Pro: two searches
    flats = container.searches.create(user, make_search(name="Flats"))
    rent = container.searches.create(user, make_search(name="Rent", deal_type=DealType.RENT, max_price=4000, min_area=25))
    connect(container, user, 1)  # private chat: everything
    connect(container, user, -50, flats.id, "Flats group")  # connecting sends what was already found
    clock.advance(days=2)
    container.searches.create(user, make_search(name="Third"))  # created after the group: not routed there
    container.scanner.run()
    by_chat = {}
    for message in telegram.outbox:
        by_chat.setdefault(message.chat_id, set()).add(message.text)
    group_text = " ".join(by_chat.get("-50", []))
    assert "Flats" in group_text and "Third" not in group_text and "Rent" not in group_text
    assert "Third" in " ".join(by_chat["1"])
    assert rent.id  # the rent search exists, just never routed to the group


def test_turning_a_search_off_for_an_all_searches_chat(container, sign_in, telegram, client):
    user = sign_in("admin@metravo.test")
    first = container.searches.create(user, make_search(name="First"))
    second = container.searches.create(user, make_search(name="Second"))
    connect(container, user, 7)
    container.telegram_links.route(user, "7", first.id, False, [first.id, second.id])
    chat = container.telegram_links.chat("7")
    assert chat.only_selected
    assert [c.chat_id for c in container.telegram_links.receivers(user, first.id)] == []
    assert [c.chat_id for c in container.telegram_links.receivers(user, second.id)] == ["7"]
    container.telegram_links.route(user, "7", first.id, True, [first.id, second.id])
    assert [c.chat_id for c in container.telegram_links.receivers(user, first.id)] == ["7"]


def test_deleting_a_search_drops_its_routes(container, sign_in):
    user = sign_in()
    search = container.searches.create(user, make_search())
    connect(container, user, -9, search.id)
    container.searches.delete(user, search.id)
    assert container.control_db.query("SELECT * FROM telegram_routes") == []


def test_the_search_page_lists_chats_and_switches_them(client, container, sign_in):
    token = container.auth.sign_in("dev", "anna@example.com").token
    user = sign_in()
    search = container.searches.create(user, make_search())
    connect(container, user, 5, title="Me")
    headers = {"Authorization": f"Bearer {token}"}
    chats = client.get(f"/api/telegram/searches/{search.id}/chats", headers=headers).json()
    assert [(chat["chat_id"], chat["receives"]) for chat in chats] == [("5", True)]
    changed = client.put(f"/api/telegram/chats/5/searches/{search.id}", json={"receives": False}, headers=headers).json()
    assert changed["receives"] is False and changed["only_selected"] is True
    link = client.post("/api/telegram/link", json={"search_id": search.id}, headers=headers)
    assert link.status_code == 200 and "startgroup=" in link.json()["group_url"]


def test_someone_elses_search_cannot_be_routed_or_linked(client, container, sign_in):
    other = container.searches.create(sign_in("b@x.pl"), make_search())
    token = container.auth.sign_in("dev", "anna@example.com").token
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/telegram/link", json={"search_id": other.id}, headers=headers).status_code == 404
    assert client.get(f"/api/telegram/searches/{other.id}/chats", headers=headers).status_code == 404


def test_each_card_names_its_search(container, sign_in, telegram):
    user = sign_in()
    connect(container, user, 3)
    container.searches.create(user, make_search(name="Blisko pracy"))
    container.scanner.run()
    cards = [message.text for message in telegram.outbox if "zł" in message.text]
    assert len(cards) > 1 and all("Blisko pracy" in card for card in cards)


def test_a_channel_is_connected_by_posting_the_code(container, sign_in, telegram):
    user = sign_in()
    search = container.searches.create(user, make_search(name="Kanał"))
    link = container.telegram_links.create_link(user, search.id)
    assert "startchannel" in link.channel_url and link.channel_code == f"/start {link.token}"
    container.telegram_dispatcher.handle({"channel_post": {"text": link.channel_code, "chat": {"id": -1001, "title": "Mieszkania"}}})
    chat = container.telegram_links.chat("-1001")
    assert chat.title == "Mieszkania" and chat.only_selected
    assert [c.chat_id for c in container.telegram_links.receivers(user, search.id)] == ["-1001"]
