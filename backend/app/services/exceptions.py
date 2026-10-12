"""Exception (OS&D) helpers, including converting a shipment's
data_quality_flags (set by the Batch 4 state machine) into exception rows.

The flag list on the shipment is kept for quick filtering; conversion creates one
data_quality exception per flag code that doesn't already have an open exception.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.billing import (
    Exception_,
    ExceptionSeverity,
    ExceptionSource,
    ExceptionStatus,
    ExceptionType,
)
from app.models.shipment import Shipment


def open_exception(db: Session, shipment_id: int, *, type_: ExceptionType, severity: ExceptionSeverity,
                   description: str, source: ExceptionSource = ExceptionSource.system,
                   opened_by: str = "", dq_code: str | None = None) -> Exception_:
    exc = Exception_(
        shipment_id=shipment_id, type=type_, severity=severity, status=ExceptionStatus.open,
        description=description, source=source, opened_by=opened_by, dq_code=dq_code,
        opened_at=datetime.now(timezone.utc),
    )
    db.add(exc)
    db.flush()
    return exc


def resolve_exception(db: Session, exc: Exception_, notes: str, resolved_by: str) -> None:
    exc.status = ExceptionStatus.resolved
    exc.resolved_at = datetime.now(timezone.utc)
    exc.resolved_by = resolved_by
    exc.resolution_notes = notes


_DQ_SEVERITY = {
    "IMPOSSIBLE_SEQUENCE": ExceptionSeverity.high,
    "LATE_OR_OUT_OF_ORDER": ExceptionSeverity.low,
    "BAD_POSTAL": ExceptionSeverity.medium,
    "DIMS_UNKNOWN": ExceptionSeverity.low,
    "COUNTRY_NONCANONICAL": ExceptionSeverity.low,
    "POD_WITHOUT_DELIVERY": ExceptionSeverity.medium,
}


def convert_data_quality_flags(db: Session, shipment: Shipment) -> int:
    """Create data_quality exceptions for the shipment's flags that don't already
    have an open exception with the same dq_code. Returns count created."""
    flags = shipment.data_quality_flags or []
    if not flags:
        return 0
    existing_codes = {
        e.dq_code for e in db.scalars(
            select(Exception_).where(
                Exception_.shipment_id == shipment.id,
                Exception_.type == ExceptionType.data_quality,
                Exception_.status != ExceptionStatus.resolved,
            )
        )
    }
    created = 0
    for flag in flags:
        code = flag.get("code")
        if not code or code in existing_codes:
            continue
        open_exception(
            db, shipment.id, type_=ExceptionType.data_quality,
            severity=_DQ_SEVERITY.get(code, ExceptionSeverity.medium),
            description=f"{code}: {flag.get('detail', '')}",
            source=ExceptionSource.system, dq_code=code,
        )
        existing_codes.add(code)
        created += 1
    return created
