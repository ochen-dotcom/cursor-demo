from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class PaymentStatus(str, Enum):
    CREATED = "created"
    PENDING_PROVIDER = "pending_provider"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


ALLOWED_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.CREATED: {PaymentStatus.PENDING_PROVIDER, PaymentStatus.CANCELED},
    PaymentStatus.PENDING_PROVIDER: {
        PaymentStatus.SUCCEEDED,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELED,
    },
    PaymentStatus.SUCCEEDED: set(),
    PaymentStatus.FAILED: set(),
    PaymentStatus.CANCELED: set(),
}


@dataclass(frozen=True)
class Payment:
    payment_id: str
    amount_minor: int
    currency: str
    status: PaymentStatus
    provider_reference: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.amount_minor <= 0:
            raise ValueError("amount_minor must be positive")
        if len(self.currency) != 3:
            raise ValueError("currency must be a 3-letter code")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def can_transition(from_status: PaymentStatus, to_status: PaymentStatus) -> bool:
    return to_status in ALLOWED_TRANSITIONS[from_status]


def transition(payment: Payment, to_status: PaymentStatus) -> Payment:
    if not can_transition(payment.status, to_status):
        raise ValueError(f"invalid transition: {payment.status} -> {to_status}")
    return Payment(
        payment_id=payment.payment_id,
        amount_minor=payment.amount_minor,
        currency=payment.currency,
        status=to_status,
        provider_reference=payment.provider_reference,
        created_at=payment.created_at or now_utc(),
        updated_at=now_utc(),
    )
