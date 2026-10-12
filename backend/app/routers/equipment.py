from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.equipment import (
    AttachedToType,
    DeviceStatus,
    TelematicsDevice,
    TelematicsProvider,
    Tractor,
    TractorStatus,
    Trailer,
    TrailerStatus,
    TrailerType,
)
from app.models.location import Location
from app.schemas.common import Page
from app.schemas.equipment import (
    DeviceCreate,
    DeviceOut,
    DeviceUpdate,
    TractorCreate,
    TractorOut,
    TractorUpdate,
    TrailerCreate,
    TrailerOut,
    TrailerUpdate,
)
from app.services.auth import require_staff
from app.services.crud import apply_search, clamp_page, ensure_unique, paginate
from app.services.equipment import attach_device, detach_device_from_asset
from app.services.refs import ensure_exists

router = APIRouter(prefix="/equipment", tags=["equipment"], dependencies=[Depends(require_staff)])


# ══════════════ Telematics devices ══════════════
@router.get("/devices", response_model=Page[DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    provider: TelematicsProvider | None = None,
    status: DeviceStatus | None = None,
    include_inactive: bool = False,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(TelematicsDevice)
    if status is not None:
        stmt = stmt.where(TelematicsDevice.status == status)
    elif not include_inactive:
        stmt = stmt.where(TelematicsDevice.status != DeviceStatus.inactive)
    if provider is not None:
        stmt = stmt.where(TelematicsDevice.provider == provider)
    stmt = apply_search(stmt, q, [TelematicsDevice.device_serial])
    stmt = stmt.order_by(TelematicsDevice.device_serial)
    items, total = paginate(db, stmt, p, ps)
    return Page[DeviceOut](items=items, total=total, page=p, page_size=ps)


@router.post("/devices", response_model=DeviceOut, status_code=201)
def create_device(body: DeviceCreate, db: Session = Depends(get_db)):
    ensure_unique(db, TelematicsDevice, TelematicsDevice.device_serial, body.device_serial, "device_serial")
    obj = TelematicsDevice(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/devices/{device_id}", response_model=DeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db)):
    obj = db.get(TelematicsDevice, device_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Device not found.")
    return obj


@router.patch("/devices/{device_id}", response_model=DeviceOut)
def update_device(device_id: int, body: DeviceUpdate, db: Session = Depends(get_db)):
    obj = db.get(TelematicsDevice, device_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Device not found.")
    data = body.model_dump(exclude_unset=True)
    if "device_serial" in data and data["device_serial"] != obj.device_serial:
        ensure_unique(db, TelematicsDevice, TelematicsDevice.device_serial, data["device_serial"], "device_serial", exclude_id=obj.id)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/devices/{device_id}", response_model=DeviceOut)
def deactivate_device(device_id: int, db: Session = Depends(get_db)):
    obj = db.get(TelematicsDevice, device_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Device not found.")
    obj.status = DeviceStatus.inactive
    db.commit()
    db.refresh(obj)
    return obj


# ══════════════ Tractors ══════════════
@router.get("/tractors", response_model=Page[TractorOut])
def list_tractors(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    status: TractorStatus | None = None,
    home_terminal_id: int | None = None,
    include_out_of_service: bool = True,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(Tractor)
    if status is not None:
        stmt = stmt.where(Tractor.status == status)
    if home_terminal_id is not None:
        stmt = stmt.where(Tractor.home_terminal_id == home_terminal_id)
    stmt = apply_search(stmt, q, [Tractor.unit_number, Tractor.vin, Tractor.plate])
    stmt = stmt.order_by(Tractor.unit_number)
    items, total = paginate(db, stmt, p, ps)
    return Page[TractorOut](items=items, total=total, page=p, page_size=ps)


@router.post("/tractors", response_model=TractorOut, status_code=201)
def create_tractor(body: TractorCreate, db: Session = Depends(get_db)):
    ensure_unique(db, Tractor, Tractor.unit_number, body.unit_number, "unit_number")
    ensure_exists(db, Location, body.home_terminal_id, "home_terminal_id")
    device_id = body.telematics_device_id
    obj = Tractor(**body.model_dump(exclude={"telematics_device_id"}))
    db.add(obj)
    db.flush()  # get obj.id
    if device_id is not None:
        obj.telematics_device_id = device_id
        attach_device(db, device_id, AttachedToType.tractor, obj.id)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/tractors/{tractor_id}", response_model=TractorOut)
def get_tractor(tractor_id: int, db: Session = Depends(get_db)):
    obj = db.get(Tractor, tractor_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Tractor not found.")
    return obj


@router.patch("/tractors/{tractor_id}", response_model=TractorOut)
def update_tractor(tractor_id: int, body: TractorUpdate, db: Session = Depends(get_db)):
    obj = db.get(Tractor, tractor_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Tractor not found.")
    data = body.model_dump(exclude_unset=True)
    if "unit_number" in data and data["unit_number"] != obj.unit_number:
        ensure_unique(db, Tractor, Tractor.unit_number, data["unit_number"], "unit_number", exclude_id=obj.id)
    if "home_terminal_id" in data:
        ensure_exists(db, Location, data["home_terminal_id"], "home_terminal_id")

    device_change = "telematics_device_id" in data
    new_device_id = data.pop("telematics_device_id", None) if device_change else None
    for k, v in data.items():
        setattr(obj, k, v)

    if device_change:
        if new_device_id is None:
            detach_device_from_asset(db, AttachedToType.tractor, obj.id)
            obj.telematics_device_id = None
        else:
            obj.telematics_device_id = new_device_id
            attach_device(db, new_device_id, AttachedToType.tractor, obj.id)

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/tractors/{tractor_id}", response_model=TractorOut)
def retire_tractor(tractor_id: int, db: Session = Depends(get_db)):
    obj = db.get(Tractor, tractor_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Tractor not found.")
    obj.status = TractorStatus.out_of_service
    db.commit()
    db.refresh(obj)
    return obj


# ══════════════ Trailers ══════════════
@router.get("/trailers", response_model=Page[TrailerOut])
def list_trailers(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    status: TrailerStatus | None = None,
    type: TrailerType | None = None,
    home_terminal_id: int | None = None,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(Trailer)
    if status is not None:
        stmt = stmt.where(Trailer.status == status)
    if type is not None:
        stmt = stmt.where(Trailer.type == type)
    if home_terminal_id is not None:
        stmt = stmt.where(Trailer.home_terminal_id == home_terminal_id)
    stmt = apply_search(stmt, q, [Trailer.trailer_number])
    stmt = stmt.order_by(Trailer.trailer_number)
    items, total = paginate(db, stmt, p, ps)
    return Page[TrailerOut](items=items, total=total, page=p, page_size=ps)


@router.post("/trailers", response_model=TrailerOut, status_code=201)
def create_trailer(body: TrailerCreate, db: Session = Depends(get_db)):
    ensure_unique(db, Trailer, Trailer.trailer_number, body.trailer_number, "trailer_number")
    ensure_exists(db, Location, body.home_terminal_id, "home_terminal_id")
    ensure_exists(db, Location, body.current_location_id, "current_location_id")
    device_id = body.telematics_device_id
    obj = Trailer(**body.model_dump(exclude={"telematics_device_id"}))
    db.add(obj)
    db.flush()
    if device_id is not None:
        obj.telematics_device_id = device_id
        attach_device(db, device_id, AttachedToType.trailer, obj.id)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/trailers/{trailer_id}", response_model=TrailerOut)
def get_trailer(trailer_id: int, db: Session = Depends(get_db)):
    obj = db.get(Trailer, trailer_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Trailer not found.")
    return obj


@router.patch("/trailers/{trailer_id}", response_model=TrailerOut)
def update_trailer(trailer_id: int, body: TrailerUpdate, db: Session = Depends(get_db)):
    obj = db.get(Trailer, trailer_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Trailer not found.")
    data = body.model_dump(exclude_unset=True)
    if "trailer_number" in data and data["trailer_number"] != obj.trailer_number:
        ensure_unique(db, Trailer, Trailer.trailer_number, data["trailer_number"], "trailer_number", exclude_id=obj.id)
    if "home_terminal_id" in data:
        ensure_exists(db, Location, data["home_terminal_id"], "home_terminal_id")
    if "current_location_id" in data:
        ensure_exists(db, Location, data["current_location_id"], "current_location_id")

    device_change = "telematics_device_id" in data
    new_device_id = data.pop("telematics_device_id", None) if device_change else None
    for k, v in data.items():
        setattr(obj, k, v)

    if device_change:
        if new_device_id is None:
            detach_device_from_asset(db, AttachedToType.trailer, obj.id)
            obj.telematics_device_id = None
        else:
            obj.telematics_device_id = new_device_id
            attach_device(db, new_device_id, AttachedToType.trailer, obj.id)

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/trailers/{trailer_id}", response_model=TrailerOut)
def retire_trailer(trailer_id: int, db: Session = Depends(get_db)):
    obj = db.get(Trailer, trailer_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Trailer not found.")
    obj.status = TrailerStatus.out_of_service
    db.commit()
    db.refresh(obj)
    return obj


# ══════════════ Cross-domain views (operations) ══════════════
@router.get("/trailers/{trailer_id}/contents")
def trailer_contents(trailer_id: int, db: Session = Depends(get_db)):
    """Shipments currently loaded on the trailer (via its open/in-transit manifests)."""
    from app.models.operations import Manifest, ManifestItem, ManifestStatus
    from app.models.shipment import Shipment

    if db.get(Trailer, trailer_id) is None:
        raise APIError(404, "NOT_FOUND", "Trailer not found.")
    manifests = db.scalars(
        select(Manifest).where(
            Manifest.trailer_id == trailer_id,
            Manifest.status.in_([ManifestStatus.open, ManifestStatus.in_transit, ManifestStatus.arrived]),
        )
    ).all()
    contents = []
    for m in manifests:
        items = db.scalars(
            select(ManifestItem).where(ManifestItem.manifest_id == m.id, ManifestItem.unloaded_at.is_(None))
        )
        for it in items:
            sh = db.get(Shipment, it.shipment_id)
            if sh is not None:
                contents.append({
                    "manifest_id": m.id, "shipment_id": sh.id,
                    "probill_number": sh.probill_number, "current_status": sh.current_status.value,
                })
    return {"trailer_id": trailer_id, "contents": contents}


def _device_positions(db: Session, device_id: int | None, from_: str | None, to: str | None):
    from datetime import datetime, timezone
    from app.models.telematics import GpsPing
    if device_id is None:
        return []
    stmt = select(GpsPing).where(GpsPing.device_id == device_id)
    if from_:
        stmt = stmt.where(GpsPing.recorded_at >= datetime.fromisoformat(from_.replace("Z", "+00:00")))
    if to:
        stmt = stmt.where(GpsPing.recorded_at <= datetime.fromisoformat(to.replace("Z", "+00:00")))
    stmt = stmt.order_by(GpsPing.recorded_at)
    return [
        {"recorded_at": p.recorded_at.isoformat(), "lat": p.lat, "lng": p.lng, "speed_kph": p.speed_kph}
        for p in db.scalars(stmt)
    ]


@router.get("/tractors/{tractor_id}/positions")
def tractor_positions(tractor_id: int, db: Session = Depends(get_db),
                      from_: str | None = Query(None, alias="from"), to: str | None = None):
    obj = db.get(Tractor, tractor_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Tractor not found.")
    return {"tractor_id": tractor_id, "positions": _device_positions(db, obj.telematics_device_id, from_, to)}


@router.get("/trailers/{trailer_id}/positions")
def trailer_positions(trailer_id: int, db: Session = Depends(get_db),
                      from_: str | None = Query(None, alias="from"), to: str | None = None):
    obj = db.get(Trailer, trailer_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Trailer not found.")
    return {"trailer_id": trailer_id, "positions": _device_positions(db, obj.telematics_device_id, from_, to)}


@router.get("/tractors/{tractor_id}/current-trip")
def tractor_current_trip(tractor_id: int, db: Session = Depends(get_db)):
    from app.models.operations import Trip, TripStatus

    if db.get(Tractor, tractor_id) is None:
        raise APIError(404, "NOT_FOUND", "Tractor not found.")
    trip = db.scalar(
        select(Trip).where(
            Trip.tractor_id == tractor_id,
            Trip.status.in_([TripStatus.planned, TripStatus.dispatched, TripStatus.in_progress]),
        ).order_by(Trip.created_at.desc())
    )
    if trip is None:
        return {"tractor_id": tractor_id, "trip": None}
    return {
        "tractor_id": tractor_id,
        "trip": {"id": trip.id, "trip_number": trip.trip_number, "status": trip.status.value, "type": trip.type.value},
    }
