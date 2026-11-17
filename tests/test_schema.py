from payment_service.sqlite_repository import apply_schema
from payment_service.sqlite_repository import connect


def test_schema_tables_columns_and_indexes() -> None:
    conn = connect()
    apply_schema(conn)

    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert {"payments", "payment_status_events"} <= tables

    payment_columns = [row[1] for row in conn.execute("PRAGMA table_info(payments)")]
    assert payment_columns == [
        "payment_id",
        "amount_minor",
        "currency",
        "status",
        "provider_reference",
        "created_at",
        "updated_at",
    ]

    event_columns = [row[1] for row in conn.execute("PRAGMA table_info(payment_status_events)")]
    assert event_columns == [
        "id",
        "payment_id",
        "previous_status",
        "next_status",
        "changed_at",
    ]

    indexes = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
    }
    assert {
        "idx_payments_status",
        "idx_payments_provider_reference",
        "idx_payment_status_events_payment_id",
    } <= indexes
