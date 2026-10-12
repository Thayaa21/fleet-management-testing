from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.location import Location
from app.models.operations import Trip, TripStatus, TripTrailer
from app.models.user import User
from app.schemas.common import Page
from app.schemas.trip import HookTrailerRequest, TripCreate, TripOut, TripUpdate
from app.services.auth import get_current_user, require_staff
from app.services.crud import clamp_page, ensure_unique, paginate
from app.services.operations import arrive_trip, dispatch_trip, open_manifest_guard, resolve_trailer
from app.services.refs import ensure_exists

router = APIRouter(prefix="/trips", tags=["trips"], dependencies=[Depends(require_staff)])


def _next_trip_number(db: Session) -> str:
    n = db.scalar(select(func.count()).select_from(Trip)) or 0
    return f"TRIP{n + 1:06d}"


def _load(db: Session, trip_id: int) -> Trip:
    obj = db.get(Trip, trip_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Trip not found.")
    return obj


@router.get("", response_model=Page[TripOut])
def list_trips(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: TripStatus | None = None,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(Trip)
    if status is not None:
        stmt = stmt.where(Trip.status == status)
    stmt = stmt.order_by(Trip.created_at.desc())
    items, total = paginate(db, stmt, p, ps)
    return Page[TripOut](items=items, total=total, page=p, page_size=ps)


@router.post("", response_model=TripOut, status_code=201)
def create_trip(body: TripCreate, db: Session = Depends(get_db)):
    ensure_exists(db, Location, body.origin_location_id, "origin_location_id")
    ensure_exists(db, Location, body.destination_location_id, "destination_location_id")
    number = body.trip_number or _next_trip_number(db)
    ensure_unique(db, Trip, Trip.trip_number, number, "trip_number")
    obj = Trip(**body.model_dump(exclude={"trip_number"}), trip_number=number)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{trip_id}", response_model=TripOut)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    return _load(db, trip_id)


@router.patch("/{trip_id}", response_model=TripOut)
def update_trip(trip_id: int, body: TripUpdate, db: Session = Depends(get_db)):
    obj = _load(db, trip_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{trip_id}/trailers", response_model=TripOut, status_code=201)
def hook_trailer(trip_id: int, body: HookTrailerRequest, db: Session = Depends(get_db)):
    trip = _load(db, trip_id)
    trailer = resolve_trailer(db, body.trailer_number)
    existing = db.scalar(
        select(TripTrailer).where(TripTrailer.trip_id == trip.id, TripTrailer.trailer_id == trailer.id)
    )
    if existing is None:
        db.add(TripTrailer(trip_id=trip.id, trailer_id=trailer.id, position=body.position,
                           hooked_at=datetime.now(timezone.utc)))
    db.commit()
    db.refresh(trip)
    return trip


@router.post("/{trip_id}/dispatch", response_model=TripOut)
def dispatch(trip_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trip = _load(db, trip_id)
    dispatch_trip(db, trip, user.email)
    db.commit()
    db.refresh(trip)
    return trip


@router.post("/{trip_id}/arrive", response_model=TripOut)
def arrive(trip_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    trip = _load(db, trip_id)
    arrive_trip(db, trip, user.email)
    db.commit()
    db.refresh(trip)
    return trip
