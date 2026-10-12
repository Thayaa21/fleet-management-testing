"""Position resolution.

A shipment has no device of its own — it inherits positions from whatever trailer
(and, via the trip, tractor) carried it during each loaded window. Resolving a
shipment's track therefore means:

  1. Find every loaded segment: a manifest_item with loaded_at set. The window is
     [loaded_at, unloaded_at or now]; the carrying trailer is the manifest's
     trailer. This naturally splits at a terminal trailer change (unload from A
     closes one window, load on B opens the next).
  2. For each window, resolve the tractor from the trip that trailer was on during
     the window (trip_trailers → trips), if any.
  3. Gather gps_pings from the trailer's device (and the tractor's device) whose
     recorded_at falls in the window; concatenate ordered by time.

This module is deliberately the single source of this logic so the agent can
reuse it verbatim.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.equipment import AttachedToType, TelematicsDevice, Tractor, Trailer
from app.models.operations import Manifest, ManifestItem, Trip, TripTrailer
from app.models.shipment import Shipment
from app.models.telematics import GpsPing


def _aware(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _device_id_for_trailer(db: Session, trailer_id: int | None) -> int | None:
    if trailer_id is None:
        return None
    trailer = db.get(Trailer, trailer_id)
    return trailer.telematics_device_id if trailer else None


def _device_id_for_tractor(db: Session, tractor_id: int | None) -> int | None:
    if tractor_id is None:
        return None
    tractor = db.get(Tractor, tractor_id)
    return tractor.telematics_device_id if tractor else None


def shipment_position_windows(db: Session, shipment: Shipment) -> list[dict]:
    """One window per loaded segment: {trailer_id, tractor_id, start, end}."""
    windows: list[dict] = []
    items = db.scalars(
        select(ManifestItem).where(ManifestItem.shipment_id == shipment.id).order_by(ManifestItem.loaded_at)
    ).all()
    now = datetime.now(timezone.utc)

    for it in items:
        if it.loaded_at is None:
            continue
        manifest = db.get(Manifest, it.manifest_id)
        if manifest is None:
            continue
        start = _aware(it.loaded_at)
        end = _aware(it.unloaded_at) or now
        trailer_id = manifest.trailer_id

        # Resolve tractor via a trip that carried this trailer overlapping the window.
        tractor_id = None
        for tt in db.scalars(select(TripTrailer).where(TripTrailer.trailer_id == trailer_id)):
            trip = db.get(Trip, tt.trip_id)
            if trip and trip.tractor_id is not None:
                dep = _aware(trip.actual_departure_at)
                arr = _aware(trip.actual_arrival_at) or now
                # Overlap check.
                if dep is None or (dep <= end and arr >= start):
                    tractor_id = trip.tractor_id
                    break

        windows.append({"trailer_id": trailer_id, "tractor_id": tractor_id, "start": start, "end": end})
    return windows


def _pings_for_device(db: Session, device_id: int | None, start: datetime, end: datetime) -> list[GpsPing]:
    if device_id is None:
        return []
    return list(
        db.scalars(
            select(GpsPing).where(
                GpsPing.device_id == device_id,
                GpsPing.recorded_at >= start,
                GpsPing.recorded_at <= end,
            ).order_by(GpsPing.recorded_at)
        )
    )


def shipment_positions(db: Session, shipment: Shipment) -> list[dict]:
    """Ordered list of position points a shipment traversed, across trailer changes."""
    points: list[dict] = []
    for w in shipment_position_windows(db, shipment):
        device_ids = {
            _device_id_for_trailer(db, w["trailer_id"]),
            _device_id_for_tractor(db, w["tractor_id"]),
        }
        for did in device_ids:
            for p in _pings_for_device(db, did, w["start"], w["end"]):
                points.append({
                    "recorded_at": p.recorded_at.isoformat() if p.recorded_at else None,
                    "lat": p.lat, "lng": p.lng, "speed_kph": p.speed_kph,
                    "trailer_id": w["trailer_id"], "tractor_id": w["tractor_id"],
                    "device_id": did,
                })
    points.sort(key=lambda x: x["recorded_at"] or "")
    return points
