import sqlite3
from datetime import datetime
from datetime import timezone

import pytest

from payment_service.repository import PaymentRecord
from payment_service.sqlite_repository import SqlitePaymentRepository
from payment_service.sqlite_repository import apply_schema
from payment_service.sqlite_repository import connect

CREATED = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)


def repository() -> SqlitePaymentRepository:
    conn = connect()
    apply_schema(conn)
    return SqlitePaymentRepository(conn)


def record(
    *,
    payment_id: str = "pay_100",
    amount_minor: int = 2300,
    currency: str = "EUR",
    status: str = "created",
    provider_reference: str | None = None,
    created_at: datetime = CREATED,
    updated_at: datetime = CREATED,
) -> PaymentRecord:
    return PaymentRecord(
        payment_id=payment_id,
        amount_minor=amount_minor,
        currency=currency,
        status=status,
        provider_reference=provider_reference,
        created_at=created_at,
        updated_at=updated_at,
    )


def test_create_and_get_round_trip() -> None:
    repo = repository()
    repo.create(record())

    stored = repo.get_by_payment_id("pay_100")
    assert stored == record()
    assert repo.get_by_payment_id("missing") is None

    events = repo.list_status_events("pay_100")
    assert len(events) == 1
    assert events[0]["previous_status"] is None
    assert events[0]["next_status"] == "created"


def test_create_rejects_invalid_payment_shape() -> None:
    repo = repository()
    with pytest.raises(ValueError, match="amount_minor"):
        repo.create(record(amount_minor=0))
    with pytest.raises(ValueError, match="currency"):
        repo.create(record(currency="EURO"))
    with pytest.raises(ValueError):
        repo.create(record(status="not-a-status"))
    assert repo.get_by_payment_id("pay_100") is None


def test_duplicate_payment_id_is_rejected() -> None:
    repo = repository()
    repo.create(record())
    with pytest.raises(sqlite3.IntegrityError):
        repo.create(record())


def test_valid_status_update_writes_history_and_keeps_reference() -> None:
    repo = repository()
    repo.create(record())

    repo.update_status(
        "pay_100",
        status="pending_provider",
        provider_reference="prov_9",
    )
    repo.update_status("pay_100", status="succeeded")

    stored = repo.get_by_payment_id("pay_100")
    assert stored is not None
    assert stored.status == "succeeded"
    assert stored.provider_reference == "prov_9"
    assert stored.created_at == CREATED
    assert stored.updated_at is not None
    assert stored.updated_at > CREATED

    events = repo.list_status_events("pay_100")
    assert [(event["previous_status"], event["next_status"]) for event in events] == [
        (None, "created"),
        ("created", "pending_provider"),
        ("pending_provider", "succeeded"),
    ]


def test_invalid_transition_does_not_change_payment_or_history() -> None:
    repo = repository()
    repo.create(record())

    with pytest.raises(ValueError, match="invalid transition"):
        repo.update_status("pay_100", status="succeeded", provider_reference="prov_x")

    stored = repo.get_by_payment_id("pay_100")
    assert stored == record()
    assert len(repo.list_status_events("pay_100")) == 1


def test_update_missing_payment_raises() -> None:
    repo = repository()
    with pytest.raises(KeyError):
        repo.update_status("missing", status="canceled")
