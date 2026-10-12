"""Freight bill generation. A draft bill is created when a shipment is DELIVERED;
staff review and issue it."""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.billing import FreightBill, FreightBillStatus
from app.models.shipment import Shipment
from app.services.rating import rate_shipment


def _next_bill_number(db: Session) -> str:
    n = db.scalar(select(func.count()).select_from(FreightBill)) or 0
    return f"FB{n + 1:07d}"


def generate_draft_for(db: Session, shipment: Shipment) -> FreightBill | None:
    """Create a draft freight bill for a delivered shipment (idempotent — skips if
    a non-void bill already exists)."""
    existing = db.scalar(
        select(FreightBill).where(
            FreightBill.shipment_id == shipment.id,
            FreightBill.status != FreightBillStatus.void,
        )
    )
    if existing is not None:
        return existing

    rated = rate_shipment(db, shipment)
    tax = 0.0  # simple config placeholder
    bill = FreightBill(
        shipment_id=shipment.id,
        bill_number=_next_bill_number(db),
        bill_to_customer_id=shipment.customer_id,
        line_items=rated["line_items"],
        subtotal=rated["subtotal"],
        fuel_surcharge=rated["fuel_surcharge"],
        accessorials_total=rated["accessorials_total"],
        tax=tax,
        total=round(rated["total"] + tax, 2),
        status=FreightBillStatus.draft,
    )
    db.add(bill)
    db.flush()
    return bill


def issue_bill(db: Session, bill: FreightBill) -> None:
    bill.status = FreightBillStatus.issued
    bill.issued_at = datetime.now(timezone.utc)
