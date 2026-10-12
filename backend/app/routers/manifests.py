from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.location import Location
from app.models.operations import Manifest, ManifestItem, ManifestStatus
from app.models.user import User
from app.schemas.common import Page
from app.schemas.manifest import (
    LoadRequest,
    ManifestCreate,
    ManifestItemOut,
    ManifestOut,
    UnloadRequest,
)
from app.services.auth import get_current_user, require_staff
from app.services.crud import clamp_page, paginate
from app.services.operations import (
    load_shipment,
    open_manifest_guard,
    resolve_shipment,
    resolve_trailer,
    unload_shipment,
)
from app.services.refs import ensure_exists

router = APIRouter(prefix="/manifests", tags=["manifests"], dependencies=[Depends(require_staff)])


def _load(db: Session, manifest_id: int) -> Manifest:
    obj = db.get(Manifest, manifest_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Manifest not found.")
    return obj


@router.get("", response_model=Page[ManifestOut])
def list_manifests(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: ManifestStatus | None = None,
    trailer_id: int | None = None,
    trip_id: int | None = None,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(Manifest)
    if status is not None:
        stmt = stmt.where(Manifest.status == status)
    if trailer_id is not None:
        stmt = stmt.where(Manifest.trailer_id == trailer_id)
    if trip_id is not None:
        stmt = stmt.where(Manifest.trip_id == trip_id)
    stmt = stmt.order_by(Manifest.created_at.desc())
    items, total = paginate(db, stmt, p, ps)
    return Page[ManifestOut](items=items, total=total, page=p, page_size=ps)


@router.post("", response_model=ManifestOut, status_code=201)
def create_manifest(body: ManifestCreate, db: Session = Depends(get_db)):
    trailer = resolve_trailer(db, body.trailer_number)
    open_manifest_guard(db, trailer.id)
    ensure_exists(db, Location, body.origin_location_id, "origin_location_id")
    ensure_exists(db, Location, body.destination_location_id, "destination_location_id")
    obj = Manifest(
        trailer_id=trailer.id, trip_id=body.trip_id,
        origin_location_id=body.origin_location_id, destination_location_id=body.destination_location_id,
        status=ManifestStatus.open,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{manifest_id}", response_model=ManifestOut)
def get_manifest(manifest_id: int, db: Session = Depends(get_db)):
    return _load(db, manifest_id)


@router.get("/{manifest_id}/items", response_model=list[ManifestItemOut])
def list_items(manifest_id: int, db: Session = Depends(get_db)):
    _load(db, manifest_id)
    return list(db.scalars(select(ManifestItem).where(ManifestItem.manifest_id == manifest_id)))


@router.post("/{manifest_id}/load", response_model=ManifestItemOut, status_code=201)
def load(manifest_id: int, body: LoadRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    manifest = _load(db, manifest_id)
    # If a trailer_number is supplied it must resolve to this manifest's trailer.
    if body.trailer_number:
        trailer = resolve_trailer(db, body.trailer_number)
        if trailer.id != manifest.trailer_id:
            raise APIError(409, "TRAILER_MISMATCH",
                           "trailer_number does not match this manifest's trailer.",
                           {"manifest_trailer_id": manifest.trailer_id, "resolved_trailer_id": trailer.id})
    shipment = resolve_shipment(db, shipment_id=body.shipment_id, probill_number=body.probill_number)
    item = load_shipment(db, manifest, shipment, body.handling_units_loaded, user.email)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{manifest_id}/unload", response_model=ManifestItemOut)
def unload(manifest_id: int, body: UnloadRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    manifest = _load(db, manifest_id)
    shipment = resolve_shipment(db, shipment_id=body.shipment_id, probill_number=body.probill_number)
    item = unload_shipment(db, manifest, shipment, user.email)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{manifest_id}/close", response_model=ManifestOut)
def close(manifest_id: int, db: Session = Depends(get_db)):
    manifest = _load(db, manifest_id)
    manifest.status = ManifestStatus.closed
    manifest.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(manifest)
    return manifest
