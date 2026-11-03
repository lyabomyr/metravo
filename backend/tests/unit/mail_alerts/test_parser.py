from pathlib import Path

from app.services.mail_alerts.inbox import AlertMail, read_mail
from app.services.mail_alerts.parser import AlertParser
from app.services.mail_alerts.redirects import RedirectResolver

MAIL = Path(__file__).parents[2] / "fixtures" / "mail"


class NoNetwork:
    """A resolver's HTTP client that records what it was asked and fails the test on an unknown address."""

    def __init__(self, redirects: dict[str, str] | None = None):
        self.redirects, self.asked = redirects or {}, []

    def head(self, url, allow_redirects, timeout):
        self.asked.append(url)
        target = self.redirects.get(url)
        return type("Reply", (), {"status_code": 302 if target else 404, "headers": {"Location": target} if target else {}})()

    get = head


def parse(name: str, http: NoNetwork | None = None):
    mail = read_mail(name, (MAIL / name).read_bytes())
    return mail, {listing.key: listing for listing in AlertParser(RedirectResolver(http or NoNetwork())).listings(mail)}


def test_an_olx_alert_becomes_listings_with_what_the_email_shows():
    mail, listings = parse("olx-krakow.eml")
    assert mail.sender == "powiadomienia@olx.pl" and "Kraków" in mail.subject
    assert set(listings) == {"olx:Xy12Ab", "olx:Qw34Cd"}
    flat = listings["olx:Xy12Ab"]
    assert flat.title == "3 pokoje z balkonem, Krowodrza"
    assert flat.price == 649000  # not the 13 534 zł/m² next to it
    assert flat.area == 58 and flat.rooms == 3
    assert flat.url == "https://www.olx.pl/d/oferta/3-pokoje-z-balkonem-krowodrza-CID3-IDXy12Ab.html"  # no tracking
    assert flat.image_url.startswith("https://ireland.apollo.olxcdn.com/") and "xy12ab" in flat.image_url
    assert listings["olx:Qw34Cd"].price == 389000 and listings["olx:Qw34Cd"].area == 27


def test_footer_links_and_the_tracking_pixel_are_never_followed():
    http = NoNetwork()
    parse("olx-krakow.eml", http)
    assert http.asked == []  # unsubscribe and settings links are recognised without a request


def test_an_otodom_alert_with_links_wrapped_by_a_tracker():
    _, listings = parse("otodom-krakow.eml")
    assert set(listings) == {"otodom:4uAb1", "otodom:4uCd2"}
    flat = listings["otodom:4uAb1"]
    assert flat.url == "https://www.otodom.pl/pl/oferta/2-pokoje-podgorze-po-remoncie-ID4uAb1"
    assert (flat.price, flat.area, flat.rooms) == (545000, 46.5, 2)
    assert listings["otodom:4uCd2"].price == 1190000


def test_a_click_tracker_is_followed_to_the_offer_but_never_onto_it():
    offer = "https://www.otodom.pl/pl/oferta/dom-z-ogrodem-ID4zZz9"
    http = NoNetwork({"https://click.example/c/1": "https://click.example/c/2", "https://click.example/c/2": offer})
    html = '<div><a href="https://click.example/c/1">Dom z ogrodem</a><p>899 000 zł · 120 m²</p></div>'
    listings = AlertParser(RedirectResolver(http)).listings(AlertMail("1", "noreply@otodom.pl", "s", html, ""))
    assert [(item.key, item.price) for item in listings] == [("otodom:4zZz9", 899000)]
    assert offer not in http.asked  # the portal's own page is not requested


def test_a_plain_text_alert_still_gives_the_offers():
    text = "Nowe: https://www.olx.pl/d/oferta/pokoj-ID9aA.html 1 200 zł"
    listings = AlertParser(RedirectResolver(NoNetwork())).listings(AlertMail("1", "x@olx.pl", "s", "", text))
    assert [item.key for item in listings] == ["olx:9aA"]


def test_an_email_without_offers_gives_nothing():
    html = '<p>Witaj! <a href="https://www.olx.pl/">OLX</a></p>'
    assert AlertParser(RedirectResolver(NoNetwork())).listings(AlertMail("1", "x@olx.pl", "s", html, "")) == []
