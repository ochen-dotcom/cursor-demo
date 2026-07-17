from payment_service.domain import Payment
from payment_service.domain import PaymentStatus
from payment_service.domain import can_transition
from payment_service.domain import transition


def test_valid_transition_created_to_pending_provider() -> None:
    payment = Payment(
        payment_id="pay_1",
        amount_minor=1500,
        currency="USD",
        status=PaymentStatus.CREATED,
    )

    updated = transition(payment, PaymentStatus.PENDING_PROVIDER)
    assert updated.status == PaymentStatus.PENDING_PROVIDER


def test_invalid_terminal_transition() -> None:
    payment = Payment(
        payment_id="pay_2",
        amount_minor=1500,
        currency="USD",
        status=PaymentStatus.SUCCEEDED,
    )

    assert not can_transition(PaymentStatus.SUCCEEDED, PaymentStatus.FAILED)

    try:
        transition(payment, PaymentStatus.FAILED)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "invalid transition" in str(exc)
