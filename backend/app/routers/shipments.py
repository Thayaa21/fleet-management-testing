from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.audit import AuditAction
from app.models.customer import Customer
from app.models.location import Location
from app.models.milestone import Milestone
from app.models.shipment import HandlingUnit, Shipment, ShipmentStatus
from app.models.user import User
from app.schemas.common import Page
from app.schemas.handling_unit import HandlingUnitCreate, HandlingUnitOut
from app.schemas.milestone import MilestoneCreate, MilestoneOut
from app.schemas.shipment import (
    CancelRequest,
    ShipmentCreate,
    ShipmentDetail,
    ShipmentOut,
    ShipmentUpdate,
)
from app.services.audit import record_audit
from app.services.auth import get_current_user, require_staff
from app.services.crud import apply_search, clamp_page, ensure_unique, paginate
from app.services.refs import ensure_exists
from app.services.shipment_state import add_milestone as sm_add_milestone

router = APIRouter(prefix="/shipments", tags=["shipments"], dependencies=[Depends(require_staff)])


def _next_probill(db: Session) -> str:
    n = db.scalar(select(func.count()).select_from(Shipment)) or 0
    return f"P{n + 1:07d}"


def _load(db: Session, shipment_id: int) -> Shipment:
    obj = db.get(Shipment, shipment_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Shipment not found.")
    return obj


@router.get("", response_model=Page[ShipmentOut])
def list_shipments(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    status: ShipmentStatus | None = None,
    customer_id: int | None = None,
    origin_terminal_id: int | None = None,
    destination_terminal_id: int | None = None,
    pickup_from: str | None = None,
    pickup_to: str | None = None,
    has_data_quality_flags: bool | None = None,
    stale_for_hours: int | None = None,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(Shipment)
    if status is not None:
        stmt = stmt.where(Shipment.current_status == status)
    if customer_id is not None:
        stmt = stmt.where(Shipment.customer_id == customer_id)
    if origin_terminal_id is not None:
        stmt = stmt.where(Shipment.shipper_location_id == origin_terminal_id)
    if destination_terminal_id is not None:
        stmt = stmt.where(Shipment.consignee_location_id == destination_terminal_id)
    if pickup_from:
        stmt = stmt.where(Shipment.pickup_date >= pickup_from)
    if pickup_to:
        stmt = stmt.where(Shipment.pickup_date <= pickup_to)
    if has_data_quality_flags is True:
        stmt = stmt.where(Shipment.data_quality_flags != [])
    stmt = apply_search(stmt, q, [Shipment.probill_number, Shipment.bol_number, Shipment.customer_reference])

    if stale_for_hours is not None:
        # Shipments with no milestone in N hours while not delivered/cancelled.
        cutoff = datetime.now(timezone.utc) - timedelta(hours=stale_for_hours)
        latest = (
            select(Milestone.shipment_id, func.max(Milestone.event_at).label("last_at"))
            .where(Milestone.is_voided.is_(False))
            .group_by(Milestone.shipment_id)
            .subquery()
        )
        stmt = (
            stmt.outerjoin(latest, latest.c.shipment_id == Shipment.id)
            .where(Shipment.current_status.notin_([ShipmentStatus.DELIVERED, ShipmentStatus.CANCELLED]))
            .where(func.coalesce(latest.c.last_at, Shipment.created_at) < cutoff)
        )

    stmt = stmt.order_by(Shipment.created_at.desc())
    items, total = paginate(db, stmt, p, ps)
    return Page[ShipmentOut](items=items, total=total, page=p, page_size=ps)


@router.post("", response_model=ShipmentOut, status_code=201)
def create_shipment(body: ShipmentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_exists(db, Customer, body.customer_id, "customer_id")
    ensure_exists(db, Location, body.shipper_location_id, "shipper_location_id")
    ensure_exists(db, Location, body.consignee_location_id, "consignee_location_id")

    probill = body.probill_number or _next_probill(db)
    ensure_unique(db, Shipment, Shipment.probill_number, probill, "probill_number")

    data = body.model_dump(exclude={"probill_number"})
    obj = Shipment(**data, probill_number=probill, created_by=user.email)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{shipment_id}", response_model=ShipmentDetail)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    obj = _load(db, shipment_id)
    units = list(db.scalars(select(HandlingUnit).where(HandlingUnit.shipment_id == shipment_id)))
    milestones = list(
        db.scalars(
            select(Milestone).where(Milestone.shipment_id == shipment_id).order_by(Milestone.event_at)
        )
    )
    detail = ShipmentDetail.model_validate(obj)
    detail.handling_units = [HandlingUnitOut.model_validate(u) for u in units]
    detail.milestones = [MilestoneOut.model_validate(m) for m in milestones]
    return detail


@router.patch("/{shipment_id}", response_model=ShipmentOut)
def update_shipment(shipment_id: int, body: ShipmentUpdate, db: Session = Depends(get_db)):
    obj = _load(db, shipment_id)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{shipment_id}/cancel", response_model=ShipmentOut)
def cancel_shipment(shipment_id: int, body: CancelRequest, db: Session = Depends(get_db)):
    obj = _load(db, shipment_id)
    if obj.current_status == ShipmentStatus.DELIVERED:
        raise APIError(409, "INVALID_STATE", "A delivered shipment cannot be cancelled.")
    obj.current_status = ShipmentStatus.CANCELLED
    record_audit(db, entity_type="shipments", entity_id=obj.id, action=AuditAction.cancel, reason=body.reason)
    db.commit()
    db.refresh(obj)
    return obj


# ── Handling units ──
@router.get("/{shipment_id}/handling-units", response_model=list[HandlingUnitOut])
def list_handling_units(shipment_id: int, db: Session = Depends(get_db)):
    _load(db, shipment_id)
    return list(db.scalars(select(HandlingUnit).where(HandlingUnit.shipment_id == shipment_id)))


@router.post("/{shipment_id}/handling-units", response_model=HandlingUnitOut, status_code=201)
def add_handling_unit(shipment_id: int, body: HandlingUnitCreate, db: Session = Depends(get_db)):
    _load(db, shipment_id)
    if body.label_barcode:
        ensure_unique(db, HandlingUnit, HandlingUnit.label_barcode, body.label_barcode, "label_barcode")
    obj = HandlingUnit(**body.model_dump(), shipment_id=shipment_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Milestones ──
@router.get("/{shipment_id}/milestones", response_model=list[MilestoneOut])
def list_milestones(shipment_id: int, include_voided: bool = False, db: Session = Depends(get_db)):
    _load(db, shipment_id)
    stmt = select(Milestone).where(Milestone.shipment_id == shipment_id)
    if not include_voided:
        stmt = stmt.where(Milestone.is_voided.is_(False))
    return list(db.scalars(stmt.order_by(Milestone.event_at)))


@router.post("/{shipment_id}/milestones", response_model=ShipmentDetail, status_code=201)
def add_milestone(shipment_id: int, body: MilestoneCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = _load(db, shipment_id)
    ensure_exists(db, Location, body.location_id, "location_id")
    sm_add_milestone(
        db, obj,
        event_code=body.event_code, source=body.source, event_at=body.event_at,
        location_id=body.location_id, lat=body.lat, lng=body.lng,
        trailer_id=body.trailer_id, tractor_id=body.tractor_id, driver_id=body.driver_id,
        edi_214_code=body.edi_214_code, notes=body.notes, created_by=user.email,
    )
    db.commit()
    db.refresh(obj)
    return get_shipment(shipment_id, db)


# ── Positions ──
@router.get("/{shipment_id}/positions")
def positions(shipment_id: int, db: Session = Depends(get_db)):
    from app.services.positions import shipment_position_windows, shipment_positions
    obj = _load(db, shipment_id)
    return {
        "shipment_id": shipment_id,
        "windows": [
            {**w, "start": w["start"].isoformat() if w["start"] else None,
             "end": w["end"].isoformat() if w["end"] else None}
            for w in shipment_position_windows(db, obj)
        ],
        "positions": shipment_positions(db, obj),
    }


# ── Timeline ──
@router.get("/{shipment_id}/timeline")
def timeline(shipment_id: int, db: Session = Depends(get_db)):
    from app.models.audit import AuditLog
    _load(db, shipment_id)
    milestones = list(
        db.scalars(
            select(Milestone).where(Milestone.shipment_id == shipment_id, Milestone.is_voided.is_(False))
            .order_by(Milestone.event_at)
        )
    )
    audits = list(
        db.scalars(
            select(AuditLog).where(AuditLog.entity_type == "shipments", AuditLog.entity_id == shipment_id)
            .order_by(AuditLog.created_at)
        )
    )
    return {
        "milestones": [MilestoneOut.model_validate(m).model_dump() for m in milestones],
        "audit": [
            {"id": a.id, "action": a.action.value, "actor_type": a.actor_type.value,
             "actor_id": a.actor_id, "reason": a.reason, "created_at": a.created_at.isoformat()}
            for a in audits
        ],
    }
