"""Operations business logic: equipment resolution, loading/unloading, and trip
dispatch/arrival milestone propagation.

All shipment status changes flow through Batch 4's add_milestone so status
recomputation, EDI codes, data-quality flags, and auditing stay consistent.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import APIError
from app.models.equipment import Trailer, TrailerStatus
from app.models.milestone import EventCode, MilestoneSource
from app.models.operations import (
    Manifest,
    ManifestItem,
    ManifestStatus,
    Trip,
    TripStatus,
    TripTrailer,
)
from app.models.shipment import Shipment
from app.services.shipment_state import add_milestone

OPEN_MANIFEST_STATES = (ManifestStatus.open, ManifestStatus.in_transit)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Fuzzy equipment resolution ────────────────────────────
def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def resolve_trailer(db: Session, trailer_number: str) -> Trailer:
    """Resolve a trailer by number. On miss, raise 422 UNKNOWN_EQUIPMENT_ID with
    up to 5 fuzzy candidates (Levenshtein distance <= 2). Never auto-picks."""
    number = (trailer_number or "").strip().upper()
    exact = db.scalar(select(Trailer).where(Trailer.trailer_number == number))
    if exact is not None:
        return exact

    candidates = []
    for t in db.scalars(select(Trailer).where(Trailer.status != TrailerStatus.out_of_service)):
        d = levenshtein(number, t.trailer_number)
        if d <= 2:
            candidates.append((d, t.trailer_number))
    candidates.sort(key=lambda x: (x[0], x[1]))
    raise APIError(
        422,
        "UNKNOWN_EQUIPMENT_ID",
        f"No trailer matches '{number}'.",
        {"input": number, "candidates": [c[1] for c in candidates[:5]]},
    )


def resolve_shipment(db: Session, *, shipment_id: int | None = None, probill_number: str | None = None) -> Shipment:
    obj = None
    if shipment_id is not None:
        obj = db.get(Shipment, shipment_id)
    elif probill_number:
        obj = db.scalar(select(Shipment).where(Shipment.probill_number == probill_number.strip().upper()))
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Shipment not found.",
                       {"shipment_id": shipment_id, "probill_number": probill_number})
    return obj


def open_manifest_guard(db: Session, trailer_id: int, exclude_manifest_id: int | None = None) -> None:
    """A trailer may be on only one open/in-transit manifest at a time."""
    stmt = select(Manifest).where(
        Manifest.trailer_id == trailer_id,
        Manifest.status.in_(OPEN_MANIFEST_STATES),
    )
    if exclude_manifest_id is not None:
        stmt = stmt.where(Manifest.id != exclude_manifest_id)
    if db.scalar(stmt) is not None:
        raise APIError(409, "CONFLICT", "Trailer is already on an open manifest.",
                       {"trailer_id": trailer_id})


# ── Load / unload ─────────────────────────────────────────
def load_shipment(db: Session, manifest: Manifest, shipment: Shipment, hu_count: int, user_email: str) -> ManifestItem:
    if manifest.status not in OPEN_MANIFEST_STATES:
        raise APIError(409, "INVALID_STATE", "Manifest is not open for loading.",
                       {"manifest_status": manifest.status.value})

    existing = db.scalar(
        select(ManifestItem).where(
            ManifestItem.manifest_id == manifest.id,
            ManifestItem.shipment_id == shipment.id,
            ManifestItem.unloaded_at.is_(None),
        )
    )
    if existing is not None:
        raise APIError(409, "ALREADY_LOADED", "Shipment already loaded on this manifest.")

    item = ManifestItem(
        manifest_id=manifest.id,
        shipment_id=shipment.id,
        handling_units_loaded=hu_count,
        loaded_at=_utcnow(),
        loaded_by=user_email,
    )
    db.add(item)

    shipment.current_trailer_id = manifest.trailer_id
    if manifest.origin_location_id:
        shipment.current_location_id = manifest.origin_location_id

    add_milestone(
        db, shipment,
        event_code=EventCode.LOADED_ON_TRAILER, source=MilestoneSource.dock_scan,
        location_id=manifest.origin_location_id, trailer_id=manifest.trailer_id,
        notes=f"Loaded on manifest {manifest.id}", created_by=user_email,
    )
    return item


def unload_shipment(db: Session, manifest: Manifest, shipment: Shipment, user_email: str) -> ManifestItem:
    item = db.scalar(
        select(ManifestItem).where(
            ManifestItem.manifest_id == manifest.id,
            ManifestItem.shipment_id == shipment.id,
            ManifestItem.unloaded_at.is_(None),
        )
    )
    if item is None:
        raise APIError(404, "NOT_LOADED", "Shipment is not loaded on this manifest.")

    item.unloaded_at = _utcnow()
    item.unloaded_by = user_email
    shipment.current_trailer_id = None
    if manifest.destination_location_id:
        shipment.current_location_id = manifest.destination_location_id

    add_milestone(
        db, shipment,
        event_code=EventCode.UNLOADED, source=MilestoneSource.dock_scan,
        location_id=manifest.destination_location_id, trailer_id=manifest.trailer_id,
        notes=f"Unloaded from manifest {manifest.id}", created_by=user_email,
    )
    return item


# ── Trip dispatch / arrive ────────────────────────────────
def _loaded_shipments_for_trip(db: Session, trip: Trip) -> list[tuple[Manifest, Shipment]]:
    trailer_ids = [tt.trailer_id for tt in db.scalars(select(TripTrailer).where(TripTrailer.trip_id == trip.id))]
    pairs: list[tuple[Manifest, Shipment]] = []
    if not trailer_ids:
        return pairs
    manifests = db.scalars(
        select(Manifest).where(
            Manifest.trailer_id.in_(trailer_ids),
            Manifest.status.in_(OPEN_MANIFEST_STATES),
        )
    ).all()
    for m in manifests:
        items = db.scalars(
            select(ManifestItem).where(ManifestItem.manifest_id == m.id, ManifestItem.unloaded_at.is_(None))
        )
        for it in items:
            sh = db.get(Shipment, it.shipment_id)
            if sh is not None:
                pairs.append((m, sh))
    return pairs


def dispatch_trip(db: Session, trip: Trip, user_email: str) -> int:
    if trip.status in (TripStatus.completed, TripStatus.cancelled):
        raise APIError(409, "INVALID_STATE", "Trip cannot be dispatched from its current status.",
                       {"status": trip.status.value})
    trip.status = TripStatus.in_progress
    trip.actual_departure_at = _utcnow()

    count = 0
    seen_manifests: set[int] = set()
    for manifest, shipment in _loaded_shipments_for_trip(db, trip):
        shipment.current_trip_id = trip.id
        add_milestone(
            db, shipment,
            event_code=EventCode.DEPARTED_TERMINAL, source=MilestoneSource.system,
            location_id=manifest.origin_location_id, trailer_id=manifest.trailer_id,
            notes=f"Trip {trip.trip_number} dispatched", created_by=user_email,
        )
        count += 1
        if manifest.id not in seen_manifests:
            manifest.status = ManifestStatus.in_transit
            seen_manifests.add(manifest.id)
    return count


def arrive_trip(db: Session, trip: Trip, user_email: str) -> int:
    if trip.status in (TripStatus.completed, TripStatus.cancelled):
        raise APIError(409, "INVALID_STATE", "Trip is already completed or cancelled.",
                       {"status": trip.status.value})
    trip.status = TripStatus.completed
    trip.actual_arrival_at = _utcnow()

    count = 0
    seen_manifests: set[int] = set()
    for manifest, shipment in _loaded_shipments_for_trip(db, trip):
        add_milestone(
            db, shipment,
            event_code=EventCode.ARRIVED_AT_DESTINATION_TERMINAL, source=MilestoneSource.system,
            location_id=manifest.destination_location_id or trip.destination_location_id,
            trailer_id=manifest.trailer_id,
            notes=f"Trip {trip.trip_number} arrived", created_by=user_email,
        )
        count += 1
        if manifest.id not in seen_manifests:
            manifest.status = ManifestStatus.arrived
            seen_manifests.add(manifest.id)
    return count
