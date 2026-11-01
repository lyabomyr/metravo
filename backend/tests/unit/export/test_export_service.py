import sqlite3

from tests.unit.conftest import make_search


def test_sqlite_export_is_a_complete_standalone_database(container, sign_in, tmp_path):
    user = sign_in()
    container.searches.create(user, make_search())
    container.scanner.run()

    path = tmp_path / "export.db"
    path.write_bytes(container.export.sqlite_file(user))
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM searches").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM listings").fetchone()[0] == 4


def test_csv_export_has_a_header_and_one_row_per_listing(container, sign_in):
    user = sign_in()
    container.searches.create(user, make_search())
    container.scanner.run()
    lines = container.export.listings_csv(user).strip().splitlines()
    assert lines[0].startswith("search_id,source,title,price")
    assert len(lines) == 5
