from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class PaymentRecord:
    payment_id: str
    amount_minor: int
    currency: str
    status: str
    provider_reference: str | None
    created_at: datetime
    updated_at: datetime


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class PaymentRepository(Protocol):
    def create(self, record: PaymentRecord) -> None:
        """Persist a new payment record."""

    def get_by_payment_id(self, payment_id: str) -> PaymentRecord | None:
        """Fetch one payment by internal ID."""

    def update_status(
        self,
        payment_id: str,
        *,
        status: str,
        provider_reference: str | None = None,
    ) -> None:
        """Update status and optional provider reference."""
