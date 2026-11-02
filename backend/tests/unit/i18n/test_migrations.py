from app.core.database import SqliteDatabase
from app.services.users.repository import UserRepository


def test_a_column_added_later_appears_in_an_existing_table(tmp_path):
    db = SqliteDatabase(str(tmp_path / "old.db"))
    db.execute("CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, plan TEXT NOT NULL DEFAULT 'free', "
               "created_at TEXT NOT NULL, last_login_at TEXT)")
    db.execute("INSERT INTO users (id, email, created_at) VALUES ('1', 'a@b.pl', 'now')")

    repo = UserRepository(db)
    repo.migrate()
    repo.migrate()  # twice is harmless

    assert repo.by_id("1").locale == "en"
