from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.customer import Customer
from app.models.location import Location
from app.models.operations import PickupRequest, PickupStatus
from app.schemas.common import Page
from app.schemas.pickup import PickupCreate, PickupOut, PickupUpdate
from app.services.auth import require_staff
from app.services.crud import clamp_page, paginate
from app.services.refs import ensure_exists

router = APIRouter(prefix="/pickups", tags=["pickups"], dependencies=[Depends(require_staff)])


@router.get("", response_model=Page[PickupOut])
def list_pickups(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: PickupStatus | None = None,
    location_id: int | None = None,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(PickupRequest)
    if status is not None:
        stmt = stmt.where(PickupRequest.status == status)
    if location_id is not None:
        stmt = stmt.where(PickupRequest.location_id == location_id)
    stmt = stmt.order_by(PickupRequest.requested_date, PickupRequest.id)
    items, total = paginate(db, stmt, p, ps)
    return Page[PickupOut](items=items, total=total, page=p, page_size=ps)


@router.post("", response_model=PickupOut, status_code=201)
def create_pickup(body: PickupCreate, db: Session = Depends(get_db)):
    ensure_exists(db, Customer, body.customer_id, "customer_id")
    ensure_exists(db, Location, body.location_id, "location_id")
    obj = PickupRequest(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{pickup_id}", response_model=PickupOut)
def get_pickup(pickup_id: int, db: Session = Depends(get_db)):
    obj = db.get(PickupRequest, pickup_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Pickup not found.")
    return obj


@router.patch("/{pickup_id}", response_model=PickupOut)
def update_pickup(pickup_id: int, body: PickupUpdate, db: Session = Depends(get_db)):
    obj = db.get(PickupRequest, pickup_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Pickup not found.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{pickup_id}/cancel", response_model=PickupOut)
def cancel_pickup(pickup_id: int, db: Session = Depends(get_db)):
    obj = db.get(PickupRequest, pickup_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Pickup not found.")
    obj.status = PickupStatus.cancelled
    db.commit()
    db.refresh(obj)
    return obj
