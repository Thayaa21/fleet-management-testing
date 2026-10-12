"""Shipment state machine.

Milestones are the source of truth. ``current_status`` is a cache recomputed from
the ordered, non-voided milestone history — so voiding a milestone and recomputing
yields a correct state without mutating history.

Design notes:
- Out-of-order milestones (event_at earlier than the latest) are accepted; status
  is recomputed from the full ordered history and an informational data-quality
  flag is recorded.
- Impossible sequences (e.g. DELIVERED with no prior PICKED_UP) are accepted; a
  data-quality flag is recorded and the furthest-forward implied status is taken.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditAction
from app.models.milestone import EventCode, Milestone, MilestoneSource
from app.models.shipment import Shipment, ShipmentStatus
from app.services.audit import record_audit
from app.services.edi import edi_214_for

# Which status a given event implies. Events not present here don't move status.
EVENT_TO_STATUS: dict[EventCode, ShipmentStatus] = {
    EventCode.PICKUP_DISPATCHED: ShipmentStatus.PICKUP_DISPATCHED,
    EventCode.ARRIVED_AT_PICKUP: ShipmentStatus.PICKUP_DISPATCHED,
    EventCode.PICKED_UP: ShipmentStatus.PICKED_UP,
    EventCode.ARRIVED_AT_TERMINAL: ShipmentStatus.AT_ORIGIN_TERMINAL,
    EventCode.LOADED_ON_TRAILER: ShipmentStatus.AT_ORIGIN_TERMINAL,
    EventCode.DEPARTED_TERMINAL: ShipmentStatus.IN_LINEHAUL,
    EventCode.IN_TRANSIT: ShipmentStatus.IN_LINEHAUL,
    EventCode.ARRIVED_AT_DESTINATION_TERMINAL: ShipmentStatus.AT_DESTINATION_TERMINAL,
    EventCode.UNLOADED: ShipmentStatus.AT_DESTINATION_TERMINAL,
    EventCode.OUT_FOR_DELIVERY: ShipmentStatus.OUT_FOR_DELIVERY,
    EventCode.ARRIVED_AT_DELIVERY: ShipmentStatus.OUT_FOR_DELIVERY,
    EventCode.DELIVERED: ShipmentStatus.DELIVERED,
    EventCode.EXCEPTION: ShipmentStatus.EXCEPTION,
    EventCode.CUSTOMS_HOLD: ShipmentStatus.EXCEPTION,
    EventCode.CANCELLED: ShipmentStatus.CANCELLED,
}

# Linear happy-path order used to detect forward vs backward moves.
STATUS_RANK: dict[ShipmentStatus, int] = {
    ShipmentStatus.BOOKED: 0,
    ShipmentStatus.PICKUP_DISPATCHED: 1,
    ShipmentStatus.PICKED_UP: 2,
    ShipmentStatus.AT_ORIGIN_TERMINAL: 3,
    ShipmentStatus.IN_LINEHAUL: 4,
    ShipmentStatus.AT_DESTINATION_TERMINAL: 5,
    ShipmentStatus.OUT_FOR_DELIVERY: 6,
    ShipmentStatus.DELIVERED: 7,
    # EXCEPTION / CANCELLED are off the linear axis.
}

# The linear happy path (each step's valid predecessor set is "any lower rank").
_LINEAR = [
    ShipmentStatus.BOOKED,
    ShipmentStatus.PICKUP_DISPATCHED,
    ShipmentStatus.PICKED_UP,
    ShipmentStatus.AT_ORIGIN_TERMINAL,
    ShipmentStatus.IN_LINEHAUL,
    ShipmentStatus.AT_DESTINATION_TERMINAL,
    ShipmentStatus.OUT_FOR_DELIVERY,
    ShipmentStatus.DELIVERED,
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    """Treat naive datetimes (as SQLite returns) as UTC so comparisons are safe."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def is_valid_transition(current: ShipmentStatus, target: ShipmentStatus) -> bool:
    """A transition is valid if it moves forward on the linear path, or into
    EXCEPTION/CANCELLED, or recovers from EXCEPTION to a linear state."""
    if target == current:
        return True
    if target in (ShipmentStatus.EXCEPTION, ShipmentStatus.CANCELLED):
        return current not in (ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED)
    if current == ShipmentStatus.EXCEPTION and target in STATUS_RANK:
        return True  # recover from exception
    if current in STATUS_RANK and target in STATUS_RANK:
        return STATUS_RANK[target] >= STATUS_RANK[current]
    return False


def _add_dq_flag(shipment: Shipment, code: str, detail: str) -> None:
    flags = list(shipment.data_quality_flags or [])
    flags.append({"code": code, "detail": detail, "at": _utcnow().isoformat()})
    shipment.data_quality_flags = flags


def recompute_status(shipment: Shipment, milestones: list[Milestone]) -> None:
    """Recompute shipment.current_status from ordered non-voided milestones."""
    active = [m for m in milestones if not m.is_voided]
    active.sort(key=lambda m: (_aware(m.event_at), _aware(m.recorded_at), m.id or 0))

    status = ShipmentStatus.BOOKED
    seen_ranks: set[int] = {0}

    for m in active:
        target = EVENT_TO_STATUS.get(m.event_code)
        if target is None:
            continue
        if target == ShipmentStatus.CANCELLED:
            status = ShipmentStatus.CANCELLED
            break
        if target == ShipmentStatus.EXCEPTION:
            status = ShipmentStatus.EXCEPTION
            continue
        # Recover from EXCEPTION or advance along the linear axis.
        if target in STATUS_RANK:
            # Impossible jump: DELIVERED with no evidence of pickup.
            if target == ShipmentStatus.DELIVERED and 2 not in seen_ranks:
                _add_dq_flag(shipment, "IMPOSSIBLE_SEQUENCE",
                             "DELIVERED recorded without a prior PICKED_UP milestone.")
            rank = STATUS_RANK[target]
            seen_ranks.add(rank)
            # Take the furthest-forward status implied by evidence.
            if status == ShipmentStatus.EXCEPTION or STATUS_RANK.get(status, -1) <= rank:
                status = target

    shipment.current_status = status
    if status == ShipmentStatus.DELIVERED and shipment.actual_delivery_at is None:
        # Set actual delivery from the delivering milestone if present.
        for m in active:
            if m.event_code == EventCode.DELIVERED:
                shipment.actual_delivery_at = m.event_at


def add_milestone(
    db: Session,
    shipment: Shipment,
    *,
    event_code: EventCode,
    source: MilestoneSource,
    event_at: datetime | None = None,
    location_id: int | None = None,
    lat: float | None = None,
    lng: float | None = None,
    trailer_id: int | None = None,
    tractor_id: int | None = None,
    driver_id: int | None = None,
    edi_214_code: str | None = None,
    notes: str = "",
    created_by: str = "",
) -> Milestone:
    """Append a milestone, flag out-of-order/late data, and recompute status."""
    event_at = event_at or _utcnow()

    existing = list(db.scalars(select(Milestone).where(Milestone.shipment_id == shipment.id)))
    latest_event_at = max((_aware(m.event_at) for m in existing if not m.is_voided), default=None)

    milestone = Milestone(
        shipment_id=shipment.id,
        event_code=event_code,
        event_at=event_at,
        recorded_at=_utcnow(),
        location_id=location_id,
        lat=lat,
        lng=lng,
        trailer_id=trailer_id,
        tractor_id=tractor_id,
        driver_id=driver_id,
        source=source,
        edi_214_code=edi_214_code or edi_214_for(event_code),
        notes=notes,
        created_by=created_by,
    )
    db.add(milestone)

    # Out-of-order / late: event happened before the latest known event.
    if latest_event_at is not None and _aware(event_at) < latest_event_at:
        _add_dq_flag(shipment, "LATE_OR_OUT_OF_ORDER",
                     f"{event_code.value} event_at {event_at.isoformat()} precedes latest {latest_event_at.isoformat()}.")

    db.flush()  # assign milestone.id
    recompute_status(shipment, existing + [milestone])

    # Convert any data-quality flags into exception rows (Batch 8). Local import
    # avoids a circular dependency.
    from app.services.exceptions import convert_data_quality_flags
    convert_data_quality_flags(db, shipment)

    # On delivery, generate a draft freight bill for staff to review (Batch 8).
    if shipment.current_status == ShipmentStatus.DELIVERED:
        from app.services.billing import generate_draft_for
        generate_draft_for(db, shipment)

    # Enqueue outbound webhook deliveries for this milestone (Batch 7).
    from app.services.webhooks import enqueue_deliveries
    enqueue_deliveries(db, shipment, milestone)

    return milestone


def void_milestone(db: Session, milestone: Milestone, reason: str) -> None:
    """Void a milestone (append-only correction) and recompute shipment status."""
    milestone.is_voided = True
    milestone.voided_reason = reason
    record_audit(
        db,
        entity_type="milestones",
        entity_id=milestone.id,
        action=AuditAction.void,
        reason=reason,
    )
    shipment = db.get(Shipment, milestone.shipment_id)
    remaining = list(db.scalars(select(Milestone).where(Milestone.shipment_id == shipment.id)))
    recompute_status(shipment, remaining)
