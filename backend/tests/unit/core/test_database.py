from app.core.database import SqliteDatabase, TursoDatabase, open_database, to_https


def test_sqlite_returns_rows_as_dicts():
    db = SqliteDatabase(":memory:")
    db.execute("CREATE TABLE t (id INTEGER, name TEXT)")
    assert db.execute("INSERT INTO t VALUES (?, ?)", (1, "a")) == 1
    assert db.query("SELECT * FROM t") == [{"id": 1, "name": "a"}]
    assert db.query_one("SELECT * FROM t WHERE id = 2") is None


def test_open_database_picks_engine_from_scheme(tmp_path):
    assert isinstance(open_database(f"sqlite:///{tmp_path}/x.db"), SqliteDatabase)
    assert isinstance(open_database("libsql://db.turso.io", "token"), TursoDatabase)


def test_libsql_url_becomes_https():
    assert to_https("libsql://db-org.turso.io") == "https://db-org.turso.io"


class _FakeResponse:
    def __init__(self, body):
        self._body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self._body


def test_turso_encodes_arguments_and_decodes_rows():
    db = TursoDatabase("libsql://db.turso.io", "token")
    sent = {}

    def post(url, json, timeout):
        sent.update(url=url, json=json)
        return _FakeResponse({"results": [{"type": "ok", "response": {"result": {
            "cols": [{"name": "id"}, {"name": "price"}, {"name": "title"}],
            "rows": [[{"type": "integer", "value": "7"}, {"type": "float", "value": 1.5}, {"type": "null"}]],
            "affected_row_count": 0,
        }}}]})

    db._session.post = post
    rows = db.query("SELECT * FROM t WHERE id = ?", (7,))
    assert sent["url"] == "https://db.turso.io/v2/pipeline"
    assert sent["json"]["requests"][0]["stmt"]["args"] == [{"type": "integer", "value": "7"}]
    assert rows == [{"id": 7, "price": 1.5, "title": None}]
