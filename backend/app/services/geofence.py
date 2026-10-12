"""Geofence-driven arrival milestones.

When a tractor's GPS ping lands inside the destination location's geofence while
its trip is in progress, write an ARRIVED_AT_DESTINATION_TERMINAL milestone
(source=telematics) for each loaded shipment on the trip — unless one already
exists. Gated by settings.geofence_enabled so the future agent can take it over.
"""
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.equipment import AttachedToType, TelematicsDevice, Tractor
from app.models.location import Location
from app.models.milestone import EventCode, Milestone, MilestoneSource
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

settings = get_settings()

EARTH_RADIUS_M = 6_371_000


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    return EARTH_RADIUS_M * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def maybe_geofence_arrival(db: Session, device: TelematicsDevice, lat: float, lng: float) -> int:
    """If the device's tractor is on an in-progress trip and this ping is inside
    the trip destination's geofence, write ARRIVED milestones. Returns count."""
    if not settings.geofence_enabled:
        return 0
    if device.attached_to_type != AttachedToType.tractor or device.attached_to_id is None:
        return 0

    tractor = db.get(Tractor, device.attached_to_id)
    if tractor is None:
        return 0

    trip = db.scalar(
        select(Trip).where(Trip.tractor_id == tractor.id, Trip.status == TripStatus.in_progress)
        .order_by(Trip.created_at.desc())
    )
    if trip is None or trip.destination_location_id is None:
        return 0

    dest = db.get(Location, trip.destination_location_id)
    if dest is None or dest.lat is None or dest.lng is None:
        return 0

    if haversine_m(lat, lng, dest.lat, dest.lng) > (dest.geofence_radius_m or 300):
        return 0

    # Loaded shipments on this trip's trailers' in-transit manifests.
    trailer_ids = [tt.trailer_id for tt in db.scalars(select(TripTrailer).where(TripTrailer.trip_id == trip.id))]
    if not trailer_ids:
        return 0
    manifests = db.scalars(
        select(Manifest).where(
            Manifest.trailer_id.in_(trailer_ids),
            Manifest.status.in_([ManifestStatus.open, ManifestStatus.in_transit]),
        )
    ).all()

    count = 0
    for m in manifests:
        items = db.scalars(
            select(ManifestItem).where(ManifestItem.manifest_id == m.id, ManifestItem.unloaded_at.is_(None))
        )
        for it in items:
            shipment = db.get(Shipment, it.shipment_id)
            if shipment is None:
                continue
            already = db.scalar(
                select(Milestone).where(
                    Milestone.shipment_id == shipment.id,
                    Milestone.event_code == EventCode.ARRIVED_AT_DESTINATION_TERMINAL,
                    Milestone.is_voided.is_(False),
                )
            )
            if already is not None:
                continue
            add_milestone(
                db, shipment,
                event_code=EventCode.ARRIVED_AT_DESTINATION_TERMINAL, source=MilestoneSource.telematics,
                location_id=dest.id, trailer_id=m.trailer_id, tractor_id=tractor.id,
                lat=lat, lng=lng, notes=f"Geofence arrival at {dest.name}", created_by="telematics",
            )
            count += 1
    return count
