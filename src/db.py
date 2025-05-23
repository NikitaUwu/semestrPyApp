from __future__ import annotations

import datetime as dt
import pathlib
import sqlite3
from contextlib import contextmanager
from typing import Optional # type: ignore
from importlib import resources

import src.sql

class Database:
    def __init__(self, db_path: str | pathlib.Path = "subscriptions.db") -> None:
        self.db_path = pathlib.Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None # type: ignore

    def connect(self) -> None:
        """Открывает соединение и применяет схему (если нужно)."""
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._apply_schema()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _cx(self) -> sqlite3.Connection:
        assert self._conn, "connect() not called"
        return self._conn

    def _apply_schema(self) -> None:
        """Считывает schema.sql из пакета src.sql и выполняет скрипт."""
        assert self._conn, "connect() not called"
        schema_text = resources.files(src.sql).joinpath("schema.sql").read_text(encoding="utf-8")
        self._conn.executescript(schema_text)
        self._conn.commit()

    def connection(self) -> sqlite3.Connection:
        """Возвращает активное соединение SQLite."""
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
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, cost, period, next_due.isoformat(), notes),
        )
        self._cx().commit()
        return cur.lastrowid  # type: ignore

    def get_subscription(self, sub_id: int) -> sqlite3.Row | None:
        return self._cx().execute(
            "SELECT * FROM subscription WHERE id=?", (sub_id,)
        ).fetchone()

    def list_subscriptions(self, active_only: bool = True) -> list[sqlite3.Row]:
        """
        Возвращает все подписки.
        Если active_only=True, только is_active=1, иначе все.
        """
        if active_only:
            rows = self._cx().execute(
                "SELECT * FROM subscription WHERE is_active=1 ORDER BY next_due"
            ).fetchall()
        else:
            rows = self._cx().execute(
                "SELECT * FROM subscription ORDER BY is_active DESC, next_due"
            ).fetchall()
        return rows

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
            VALUES (?, ?, ?, ?)
            """,
            (subscription_id, date_paid.isoformat(), amount, comment),
        )
        self._cx().commit()
        return cur.lastrowid  # type: ignore

    def due_soon(self, days_ahead: int = 3) -> list[sqlite3.Row]:
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
def connect(db_path: str = ":memory:"):  # type: ignore
    db = Database(db_path)
    db.connect()
    try:
        yield db
    finally:
        db.close()