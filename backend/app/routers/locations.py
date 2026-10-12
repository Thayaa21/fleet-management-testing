from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.customer import Customer
from app.models.location import Location, LocationStatus, LocationType
from app.schemas.common import Page
from app.schemas.location import LocationCreate, LocationOut, LocationUpdate
from app.services.auth import require_staff
from app.services.crud import apply_search, clamp_page, paginate
from app.services.refs import ensure_exists

router = APIRouter(prefix="/locations", tags=["locations"], dependencies=[Depends(require_staff)])


@router.get("", response_model=Page[LocationOut])
def list_locations(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    status: LocationStatus | None = None,
    type: LocationType | None = None,
    country: str | None = None,
    customer_id: int | None = None,
    include_inactive: bool = False,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(Location)
    if status is not None:
        stmt = stmt.where(Location.status == status)
    elif not include_inactive:
        stmt = stmt.where(Location.status == LocationStatus.active)
    if type is not None:
        stmt = stmt.where(Location.type == type)
    if country is not None:
        stmt = stmt.where(Location.country == country.upper())
    if customer_id is not None:
        stmt = stmt.where(Location.customer_id == customer_id)
    stmt = apply_search(stmt, q, [Location.name, Location.city, Location.postal_zip])
    stmt = stmt.order_by(Location.name)

    items, total = paginate(db, stmt, p, ps)
    return Page[LocationOut](items=items, total=total, page=p, page_size=ps)


@router.post("", response_model=LocationOut, status_code=201)
def create_location(body: LocationCreate, db: Session = Depends(get_db)):
    ensure_exists(db, Customer, body.customer_id, "customer_id")
    obj = Location(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{location_id}", response_model=LocationOut)
def get_location(location_id: int, db: Session = Depends(get_db)):
    obj = db.get(Location, location_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Location not found.")
    return obj


@router.patch("/{location_id}", response_model=LocationOut)
def update_location(location_id: int, body: LocationUpdate, db: Session = Depends(get_db)):
    obj = db.get(Location, location_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Location not found.")
    data = body.model_dump(exclude_unset=True)
    if "customer_id" in data:
        ensure_exists(db, Customer, data["customer_id"], "customer_id")
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{location_id}", response_model=LocationOut)
def deactivate_location(location_id: int, db: Session = Depends(get_db)):
    obj = db.get(Location, location_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Location not found.")
    obj.status = LocationStatus.inactive
    db.commit()
    db.refresh(obj)
    return obj
