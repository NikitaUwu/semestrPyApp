"""
db.py – слой DAL для Subscription Tracker (Python 3.13+).
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sqlite3
from contextlib import contextmanager
from typing import Optional  # type: ignore


SCHEMA_PATH = pathlib.Path(__file__).parent / "sql" / "schema.sql"


class Database:
    def __init__(self, db_path: str | pathlib.Path = "subscriptions.db") -> None:
        self.db_path = pathlib.Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None  # type: ignore

    def connect(self) -> None:
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._apply_schema()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _apply_schema(self) -> None:
        assert self._conn, "call connect() first"
        with open(SCHEMA_PATH, encoding="utf-8") as f, self._conn:
            self._conn.executescript(f.read())

    def _cx(self) -> sqlite3.Connection:
        assert self._conn, "connect() not called"
        return self._conn

    def connection(self) -> sqlite3.Connection:
        """Вернуть активное соединение SQLite (read-only для внешнего кода)."""
        return self._cx()

    def add_subscription(
        self,
        name: str,
        cost: float,
        period: str,
        next_due: dt.date,
        notes: str = "",
    ) -> int:
        cur = self._cx().execute(
            """
            INSERT INTO subscription (name, cost, period, next_due, notes)
            VALUES (?,?,?,?,?)
            """,
            (name, cost, period, next_due.isoformat(), notes),
        )
        self._cx().commit()
        return cur.lastrowid  # type: ignore

    def get_subscription(self, sub_id: int):
        return self._cx().execute(
            "SELECT * FROM subscription WHERE id=?", (sub_id,)
        ).fetchone()

    def list_subscriptions(self, active_only: bool = True) -> list[sqlite3.Row]:
        """
        Возвращает список подписок; 
        active_only=True — только активные.
        Поля: id, name, cost, period, next_due, is_active, notes.
        """
        sql = (
            "SELECT id, name, cost, period, next_due, is_active, notes "
            "FROM subscription"
        )
        if active_only:
            sql += " WHERE is_active=1"
        sql += " ORDER BY next_due"
        return self._cx().execute(sql).fetchall()

    def add_payment(
        self,
        subscription_id: int,
        date_paid: dt.date,
        amount: float,
        comment: str = "",
    ) -> int:
        cur = self._cx().execute(
            """
            INSERT INTO payment (subscription_id, date_paid, amount, comment)
            VALUES (?,?,?,?)
            """,
            (subscription_id, date_paid.isoformat(), amount, comment),
        )
        self._cx().commit()
        return cur.lastrowid  # type: ignore

    def due_soon(self, days_ahead: int = 3):
        param = f"+{days_ahead} days"
        return self._cx().execute(
            """
            SELECT * FROM subscription
            WHERE next_due <= DATE('now', ?)
              AND is_active=1
            ORDER BY next_due
            """,
            (param,),
        ).fetchall()


@contextmanager
def connect(db_path=":memory:"):  # type: ignore
    db = Database(db_path)
    db.connect()
    try:
        yield db
    finally:
        db.close()
