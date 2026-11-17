from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from payment_service.domain import Payment
from payment_service.domain import PaymentStatus
from payment_service.domain import transition
from payment_service.repository import PaymentRecord

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "db" / "schema.sql"


def connect(database: str | Path = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def _as_payment(record: PaymentRecord) -> Payment:
    return Payment(
        payment_id=record.payment_id,
        amount_minor=record.amount_minor,
        currency=record.currency,
        status=PaymentStatus(record.status),
        provider_reference=record.provider_reference,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _iso(value: datetime) -> str:
    return value.isoformat()


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


class SqlitePaymentRepository:
    """SQLite store for payments and the status-event history."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def create(self, record: PaymentRecord) -> None:
        payment = _as_payment(record)
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO payments (
                    payment_id, amount_minor, currency, status,
                    provider_reference, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payment.payment_id,
                    payment.amount_minor,
                    payment.currency,
                    payment.status.value,
                    payment.provider_reference,
                    _iso(record.created_at),
                    _iso(record.updated_at),
                ),
            )
            self._conn.execute(
                """
                INSERT INTO payment_status_events (
                    payment_id, previous_status, next_status, changed_at
                ) VALUES (?, NULL, ?, ?)
                """,
                (payment.payment_id, payment.status.value, _iso(record.created_at)),
            )

    def get_by_payment_id(self, payment_id: str) -> PaymentRecord | None:
        row = self._conn.execute(
            "SELECT * FROM payments WHERE payment_id = ?",
            (payment_id,),
        ).fetchone()
        if row is None:
            return None
        return PaymentRecord(
            payment_id=row["payment_id"],
            amount_minor=row["amount_minor"],
            currency=row["currency"],
            status=row["status"],
            provider_reference=row["provider_reference"],
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
        )

    def update_status(
        self,
        payment_id: str,
        *,
        status: str,
        provider_reference: str | None = None,
    ) -> None:
        current = self.get_by_payment_id(payment_id)
        if current is None:
            raise KeyError(payment_id)

        updated = transition(_as_payment(current), PaymentStatus(status))
        if updated.updated_at is None:
            raise RuntimeError("transition did not set updated_at")

        new_reference = (
            current.provider_reference if provider_reference is None else provider_reference
        )
        with self._conn:
            self._conn.execute(
                """
                UPDATE payments
                SET status = ?, provider_reference = ?, updated_at = ?
                WHERE payment_id = ?
                """,
                (
                    updated.status.value,
                    new_reference,
                    _iso(updated.updated_at),
                    payment_id,
                ),
            )
            self._conn.execute(
                """
                INSERT INTO payment_status_events (
                    payment_id, previous_status, next_status, changed_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    payment_id,
                    current.status,
                    updated.status.value,
                    _iso(updated.updated_at),
                ),
            )

    def list_status_events(self, payment_id: str) -> list[sqlite3.Row]:
        return list(
            self._conn.execute(
                """
                SELECT id, payment_id, previous_status, next_status, changed_at
                FROM payment_status_events
                WHERE payment_id = ?
                ORDER BY id
                """,
                (payment_id,),
            )
        )
