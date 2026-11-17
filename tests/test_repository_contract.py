from datetime import datetime
from datetime import timezone

from payment_service.repository import PaymentRecord


def test_payment_record_fields_are_stable() -> None:
    record = PaymentRecord(
        payment_id="pay_100",
        amount_minor=2300,
        currency="EUR",
        status="created",
        provider_reference=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert record.payment_id == "pay_100"
    assert record.status == "created"
    assert record.provider_reference is None
