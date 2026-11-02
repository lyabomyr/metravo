from app.services.connectors.models import Listing
from app.services.listings.models import EventKind, ListingEvent
from app.services.telegram.formatter import (
    MAX_CAPTION_LENGTH,
    MAX_LISTINGS_PER_SCAN,
    MAX_MESSAGE_LENGTH,
    ListingMessageFormatter,
)
from tests.unit.conftest import make_search


def event(n: int, image_url: str | None = None, location: str = "Długa, " + "x" * 300) -> ListingEvent:
    listing = Listing(source="otodom", external_id=str(n), url=f"https://otodom.pl/{n}", title="Mieszkanie z balkonem",
                      price=500000 + n, area=45, location=location, image_url=image_url)
    return ListingEvent(EventKind.NEW, listing)


def test_long_batches_are_split_and_capped():
    messages = ListingMessageFormatter("https://metravo.pages.dev").messages(make_search(), [event(n) for n in range(40)])
    assert all(len(message) <= MAX_MESSAGE_LENGTH for message in messages)
    text = "\n".join(messages)
    assert text.count("•") == MAX_LISTINGS_PER_SCAN
    assert f"and {40 - MAX_LISTINGS_PER_SCAN} more" in text


def test_price_is_formatted_with_spaces():
    text = ListingMessageFormatter("w").messages(make_search(), [event(1)])[0]
    assert "500 001 zł" in text


def test_each_listing_is_a_card_with_its_photo():
    cards = ListingMessageFormatter("w").cards(make_search(), [event(1, "https://img/1.jpg", "Długa"), event(2)])
    assert [card.photo for card in cards] == ["https://img/1.jpg", None]
    assert cards[0].text.startswith("🏠") and "2 new" in cards[0].text
    assert "Mieszkanie z balkonem" in cards[1].text and "🏠" not in cards[1].text


def test_cards_are_capped_and_point_to_the_rest():
    cards = ListingMessageFormatter("https://metravo.pages.dev").cards(make_search(), [event(n) for n in range(25)])
    assert len(cards) == MAX_LISTINGS_PER_SCAN + 1
    assert "and 5 more" in cards[-1].text and cards[-1].photo is None


def test_a_caption_too_long_for_a_photo_goes_as_text():
    card = ListingMessageFormatter("w").cards(make_search(), [event(1, "https://img/1.jpg", "x" * 1100)])[0]
    assert len(card.text) > MAX_CAPTION_LENGTH and card.photo is None


def test_only_web_addresses_become_photos():
    card = ListingMessageFormatter("w").cards(make_search(), [event(1, "data:image/png;base64,AAAA", "Długa")])[0]
    assert card.photo is None


def test_nothing_to_send_means_no_cards():
    assert ListingMessageFormatter("w").cards(make_search(), []) == []
