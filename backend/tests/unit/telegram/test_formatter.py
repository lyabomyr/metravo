from app.services.connectors.models import Listing
from app.services.listings.models import EventKind, ListingEvent
from app.services.telegram.formatter import MAX_LISTINGS_PER_SCAN, MAX_MESSAGE_LENGTH, ListingMessageFormatter
from tests.unit.conftest import make_search


def event(n: int) -> ListingEvent:
    listing = Listing(source="otodom", external_id=str(n), url=f"https://otodom.pl/{n}", title="t",
                      price=500000 + n, area=45, location="Długa, " + "x" * 300)
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
