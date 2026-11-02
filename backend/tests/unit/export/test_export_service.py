from tests.unit.conftest import make_search


def test_csv_export_has_a_header_and_one_row_per_listing(container, sign_in):
    user = sign_in()
    container.searches.create(user, make_search(name="Kraków 2 rooms"))
    container.scanner.run()
    lines = container.export.listings_csv(user).strip().splitlines()
    assert lines[0] == "search,source,title,price,area,rooms,price_per_m2,location,url,first_seen_at,last_seen_at"
    assert len(lines) == 5
    assert all(line.startswith("Kraków 2 rooms,") for line in lines[1:])


def test_csv_export_holds_only_the_callers_listings(container, sign_in):
    anna, ben = sign_in("anna@x.pl"), sign_in("ben@x.pl")
    container.searches.create(anna, make_search())
    container.scanner.run()
    assert len(container.export.listings_csv(ben).strip().splitlines()) == 1  # the header alone
