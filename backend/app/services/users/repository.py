from __future__ import annotations

from ...core.database import Row
from ...core.repository import BaseRepository
from .models import User


class UserRepository(BaseRepository):
    """Control database: one row per account."""

    SCHEMA = (
        """CREATE TABLE IF NOT EXISTS users (
            id            TEXT PRIMARY KEY,
            email         TEXT NOT NULL UNIQUE,
            plan          TEXT NOT NULL DEFAULT 'free',
            created_at    TEXT NOT NULL,
            last_login_at TEXT,
            locale        TEXT NOT NULL DEFAULT 'en'
        )""",
    )
    ADDED_COLUMNS = (("users", "locale", "TEXT NOT NULL DEFAULT 'en'"),)

    def by_id(self, user_id: str) -> User | None:
        return self._to_user(self._one("SELECT * FROM users WHERE id = ?", (user_id,)))

    def by_email(self, email: str) -> User | None:
        return self._to_user(self._one("SELECT * FROM users WHERE email = ?", (email,)))

    def insert(self, user_id: str, email: str, plan: str, now: str) -> None:
        self._exec(
            "INSERT INTO users (id, email, plan, created_at, last_login_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, plan, now, now),
        )

    def touch_login(self, user_id: str, now: str) -> None:
        self._exec("UPDATE users SET last_login_at = ? WHERE id = ?", (now, user_id))

    def set_locale(self, user_id: str, locale: str) -> None:
        self._exec("UPDATE users SET locale = ? WHERE id = ?", (locale, user_id))

    def set_plan(self, user_id: str, plan: str) -> None:
        self._exec("UPDATE users SET plan = ? WHERE id = ?", (plan, user_id))

    def all(self) -> list[User]:
        return [self._to_user(row) for row in self._all("SELECT * FROM users ORDER BY created_at DESC")]

    def count_by_plan(self) -> dict[str, int]:
        rows = self._all("SELECT plan, COUNT(*) AS n FROM users GROUP BY plan")
        return {row["plan"]: row["n"] for row in rows}

    @staticmethod
    def _to_user(row: Row | None) -> User | None:
        if row is None:
            return None
        return User(id=row["id"], email=row["email"], plan=row["plan"], created_at=row["created_at"], locale=row["locale"])
