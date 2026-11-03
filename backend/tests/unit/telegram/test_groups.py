from app.services.scanning.models import ScanReport
from tests.unit.conftest import make_search
from tests.unit.telegram.test_two_click_setup import update

GROUP = -4001


def connect_group(container, user, chat_id=GROUP):
    token = container.telegram_links.create_link(user).token
    # Added through the "startgroup" link, Telegram posts "/start@<bot> <token>" in the group.
    container.telegram_dispatcher.handle(update(f"/start@metravo_bot {token}", chat_id=chat_id, title="Rodzina"))


def test_a_group_is_connected_through_its_link(container, sign_in, telegram):
    user = sign_in()
    connect_group(container, user)
    chats = container.telegram_links.chats_of(user)
    assert [(chat.chat_id, chat.title) for chat in chats] == [(str(GROUP), "Rodzina")]
    assert telegram.outbox[0].chat_id == str(GROUP) and "Connected" in telegram.outbox[0].text


def test_new_listings_reach_the_group(container, sign_in, telegram):
    user = sign_in()
    connect_group(container, user)
    container.searches.create(user, make_search())
    container.scanner.run()
    listings = [message for message in telegram.outbox if message.chat_id == str(GROUP) and "zł" in message.text]
    assert listings and "new" in listings[0].text


def test_a_group_upgraded_to_a_supergroup_keeps_its_link(container, sign_in, telegram):
    user = sign_in()
    connect_group(container, user)
    container.telegram_dispatcher.handle({"message": {"chat": {"id": GROUP}, "migrate_to_chat_id": -100777}})
    assert [chat.chat_id for chat in container.telegram_links.chats_of(user)] == ["-100777"]
    container.searches.create(user, make_search())
    container.scanner.run()
    assert {message.chat_id for message in telegram.outbox if "zł" in message.text} == {"-100777"}


def test_a_failed_send_that_names_the_supergroup_moves_the_link(container, sign_in):
    user = sign_in()
    connect_group(container, user)
    container.telegram_client.on_chat_moved(str(GROUP), "-100888")  # what the HTTP client calls on that error
    assert [chat.chat_id for chat in container.telegram_links.chats_of(user)] == ["-100888"]


def test_removing_the_bot_from_a_group_disconnects_it(container, sign_in):
    user = sign_in()
    connect_group(container, user)
    container.telegram_dispatcher.handle(
        {"my_chat_member": {"chat": {"id": GROUP}, "new_chat_member": {"status": "left"}}}
    )
    assert container.telegram_links.chats_of(user) == []


def test_the_admin_page_keeps_the_last_scan_that_did_something(container):
    monitor = container.monitor
    monitor.record_scan(ScanReport(searches_scanned=2, new_listings=5))
    monitor.record_scan(ScanReport())  # a tick with nothing due
    assert monitor.status.last_scan.new_listings == 5
