"""Any city, town or village, found by name or on the map, saved with a radius."""

import pytest

from app.core.errors import Unavailable
from app.services.places.directory import PlaceDirectory
from app.services.places.http import PoliteClient
from app.services.places.models import Place
from app.services.places.nominatim import NominatimDirectory
from app.services.places.photon import PhotonDirectory

ZABIERZOW = {
    "name": "Zabierzów", "addresstype": "village", "lat": "50.1146", "lon": "19.7993",
    "address": {"village": "Zabierzów", "municipality": "gmina Zabierzów", "county": "powiat krakowski",
                "state": "województwo małopolskie"},
}
KRAKOW = {"name": "Kraków", "addresstype": "city", "lat": "50.06", "lon": "19.94",
          "address": {"city": "Kraków", "state": "województwo małopolskie"}}


class FakeHttp:
    """A requests.Session that answers every GET with the same body, or fails."""

    def __init__(self, answer, fail=False):
        self.headers, self.answer, self.fail, self.calls = {}, answer, fail, []

    def get(self, url, params=None, timeout=None):
        import requests

        self.calls.append((url, params))
        if self.fail:
            raise requests.ConnectionError("blocked")
        answer = self.answer

        class Response:
            text = answer if isinstance(answer, str) else ""

            def raise_for_status(self):
                pass

            def json(self):
                return answer

        return Response()


def nominatim(answer, fail=False):
    http = FakeHttp(answer, fail)
    return NominatimDirectory(PoliteClient("https://nominatim", 0, session=http)), http


PHOTON_BIBICE = {"features": [{"geometry": {"coordinates": [19.9552, 50.1240]},
                               "properties": {"name": "Bibice", "osm_value": "village", "countrycode": "PL"}}]}
ULDK_ZIELONKI = "0\nZielonki|powiat krakowski|małopolskie\n"
ULDK_KRAKOW = "0\nKraków (miasto)|powiat Kraków|małopolskie\n"


def test_a_village_becomes_the_path_the_portals_use():
    [place] = nominatim([ZABIERZOW])[0].search("Zabierzów")
    assert place.path == "malopolskie/krakowski/zabierzow/zabierzow"
    assert place.slug == "zabierzow" and place.region_name == "małopolskie"
    assert place.detail == "gmina Zabierzów, powiat krakowski, województwo małopolskie"


def test_a_city_with_county_rights_is_its_own_county_and_municipality():
    [place] = nominatim([KRAKOW])[0].search("Kraków")
    assert place.path == "malopolskie/krakow/krakow/krakow"


def test_lookups_are_cached_and_identify_us():
    directory, http = nominatim([ZABIERZOW])
    directory.search("Zabierzów")
    directory.search("Zabierzów")
    assert len(http.calls) == 1
    assert "Metravo" in http.headers["User-Agent"]


def test_a_point_on_the_map():
    place = nominatim(ZABIERZOW)[0].at(50.1146, 19.7993)
    assert place and place.name == "Zabierzów"


def test_a_place_outside_poland_is_not_valid():
    assert not Place("Berlin", "berlin/berlin/berlin/berlin", "Berlin", 52.52, 13.40).is_valid()


def test_places_api(client):
    token = client.post("/api/auth/session", json={"provider": "dev", "credential": "ola@x.pl"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/places?q=zab").status_code == 401  # each lookup costs OpenStreetMap a request
    found = client.get("/api/places?q=zab", headers=headers).json()
    assert [p["name"] for p in found] == ["Zabierzów"]
    assert client.get("/api/places/at?lat=50.11&lon=19.80", headers=headers).json()["name"] == "Zabierzów"


def test_a_search_keeps_its_place_and_radius(client):
    token = client.post("/api/auth/session", json={"provider": "dev", "credential": "ola@x.pl"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    [place] = client.get("/api/places?q=bibice", headers=headers).json()
    body = {"name": "Bibice", "place": place, "radius_km": 10, "max_price": 900000, "min_area": 60, "sources": ["otodom"]}
    created = client.post("/api/searches", json=body, headers=headers)
    assert created.status_code == 201, created.text
    saved = client.get("/api/searches", headers=headers).json()[0]
    assert saved["place"]["path"] == "malopolskie/krakowski/zielonki/bibice" and saved["radius_km"] == 10


def test_a_search_saved_before_places_reads_as_its_city(tmp_path):
    from app.core.database import SqliteDatabase
    from app.services.searches.repository import SearchRepository

    db = SqliteDatabase(str(tmp_path / "old.db"))
    db.execute(
        "CREATE TABLE searches (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, name TEXT NOT NULL, city TEXT NOT NULL,"
        " deal_type TEXT NOT NULL DEFAULT 'sale', property_type TEXT NOT NULL DEFAULT 'flat', min_price INTEGER,"
        " max_price INTEGER NOT NULL, min_area REAL NOT NULL, max_area REAL, min_rooms INTEGER, max_rooms INTEGER,"
        " max_price_per_m2 INTEGER, min_build_year INTEGER, sources TEXT NOT NULL, required_keywords TEXT NOT NULL DEFAULT '[]',"
        " reject_keywords TEXT NOT NULL, interval_minutes INTEGER NOT NULL DEFAULT 1440, enabled INTEGER NOT NULL DEFAULT 1,"
        " last_scanned_at TEXT, created_at TEXT NOT NULL)"
    )
    db.execute(
        "INSERT INTO searches (id, user_id, name, city, max_price, min_area, sources, reject_keywords, created_at)"
        " VALUES ('s1', 'u1', 'Old', 'krakow', 600000, 40, '[\"otodom\"]', '[]', 'now')"
    )
    SearchRepository.create_tables(db)

    [search] = SearchRepository(db, "u1").all()
    assert search.place.path == "malopolskie/krakow/krakow/krakow" and search.radius_km == 0



def test_photon_finds_the_place_and_the_geoportal_its_municipality():
    photon = PoliteClient("https://photon", 0, session=FakeHttp(PHOTON_BIBICE))
    uldk = PoliteClient("https://uldk", 0, session=FakeHttp(ULDK_ZIELONKI))
    [place] = PhotonDirectory(photon, uldk).search("Bibice")
    assert place.path == "malopolskie/krakowski/zielonki/bibice"  # Otodom 404s without the right municipality


def test_a_city_with_county_rights_from_the_geoportal():
    photon = PoliteClient("https://photon", 0, session=FakeHttp({"features": [
        {"geometry": {"coordinates": [19.94, 50.06]}, "properties": {"name": "Kraków", "osm_value": "city", "countrycode": "PL"}}]}))
    uldk = PoliteClient("https://uldk", 0, session=FakeHttp(ULDK_KRAKOW))
    assert PhotonDirectory(photon, uldk).search("Kraków")[0].path == "malopolskie/krakow/krakow/krakow"


def test_when_one_service_is_blocked_the_next_one_answers():
    blocked, _ = nominatim(None, fail=True)
    working, _ = nominatim([ZABIERZOW])
    assert [p.name for p in PlaceDirectory([blocked, working]).search("Zabierzów")] == ["Zabierzów"]


def test_every_service_down_says_so_instead_of_nothing_found():
    blocked, _ = nominatim(None, fail=True)
    with pytest.raises(Unavailable):
        PlaceDirectory([blocked]).search("Szczyrk")
    assert [p.name for p in PlaceDirectory([blocked]).search("Katowice")] == ["Katowice"]  # big cities still work
