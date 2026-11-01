"""One database interface, two engines.

``SqliteDatabase`` runs locally and in tests. ``TursoDatabase`` talks to
Turso's HTTP API — no compiled driver, so it installs on any free host.
Both return rows as plain dicts; nothing above this module knows which
engine it is talking to.
"""

from __future__ import annotations

import base64
import sqlite3
import threading
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import requests

Row = dict[str, Any]
Params = Sequence[Any]


class Database(ABC):
    """The contract every repository relies on."""

    @abstractmethod
    def execute(self, sql: str, params: Params = ()) -> int:
        """Run a statement and return the number of affected rows."""

    @abstractmethod
    def query(self, sql: str, params: Params = ()) -> list[Row]:
        """Run a SELECT and return every row."""

    def query_one(self, sql: str, params: Params = ()) -> Row | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def close(self) -> None:
        """Release resources. Optional for engines that hold none."""


class SqliteDatabase(Database):
    """SQLite file (or ``:memory:``). One connection guarded by a lock."""

    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row

    def execute(self, sql: str, params: Params = ()) -> int:
        with self._lock:
            return self._conn.execute(sql, tuple(params)).rowcount

    def query(self, sql: str, params: Params = ()) -> list[Row]:
        with self._lock:
            return [dict(row) for row in self._conn.execute(sql, tuple(params)).fetchall()]

    def close(self) -> None:
        self._conn.close()


class TursoError(RuntimeError):
    """A statement-level error reported by Turso's pipeline API."""


class TursoDatabase(Database):
    """Turso/libSQL over ``/v2/pipeline``. Every statement autocommits."""

    def __init__(self, url: str, auth_token: str, timeout: int = 30):
        self.url = url
        self._endpoint = to_https(url).rstrip("/") + "/v2/pipeline"
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        })
        self._timeout = timeout

    def execute(self, sql: str, params: Params = ()) -> int:
        return self._run(sql, params)["affected_row_count"] or 0

    def query(self, sql: str, params: Params = ()) -> list[Row]:
        result = self._run(sql, params)
        columns = [col.get("name") for col in result.get("cols") or []]
        return [
            dict(zip(columns, (_decode(cell) for cell in row), strict=False))
            for row in result.get("rows") or []
        ]

    def close(self) -> None:
        self._session.close()

    def _run(self, sql: str, params: Params) -> dict:
        statement: dict = {"sql": sql}
        if params:
            statement["args"] = [_encode(p) for p in params]
        payload = {"requests": [{"type": "execute", "stmt": statement}, {"type": "close"}]}
        response = self._session.post(self._endpoint, json=payload, timeout=self._timeout)
        response.raise_for_status()
        result = (response.json().get("results") or [{}])[0]
        if result.get("type") != "ok":
            message = (result.get("error") or {}).get("message") or "unknown error"
            raise TursoError(f"{message} — while executing: {sql.strip()[:120]}")
        return (result.get("response") or {}).get("result") or {}


def to_https(url: str) -> str:
    """``libsql://host`` → ``https://host`` (the HTTP API lives on the same host)."""
    for prefix in ("libsql://", "wss://", "ws://"):
        if url.startswith(prefix):
            return "https://" + url[len(prefix):]
    return url if url.startswith(("http://", "https://")) else "https://" + url


def open_database(url: str, token: str = "") -> Database:
    """Pick the engine from the URL scheme: ``sqlite:///path`` or ``libsql://host``."""
    if url.startswith("sqlite:///"):
        return SqliteDatabase(url[len("sqlite:///"):])
    return TursoDatabase(url, token)


def _encode(value: Any) -> dict:
    """Python value → Turso cell. Integers travel as strings (API contract)."""
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "integer", "value": str(int(value))}
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    if isinstance(value, float):
        return {"type": "float", "value": value}
    if isinstance(value, (bytes, bytearray)):
        return {"type": "blob", "base64": base64.b64encode(bytes(value)).decode("ascii")}
    return {"type": "text", "value": str(value)}


def _decode(cell: dict) -> Any:
    kind = cell.get("type")
    if kind == "null":
        return None
    if kind == "integer":
        return int(cell["value"])
    if kind == "float":
        return float(cell["value"])
    if kind == "blob":
        return base64.b64decode(cell.get("base64") or cell.get("value") or "")
    return cell.get("value")
