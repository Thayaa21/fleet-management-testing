import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin


# ── Pickup requests ───────────────────────────────────────
class PickupStatus(str, enum.Enum):
    requested = "requested"
    dispatched = "dispatched"
    completed = "completed"
    missed = "missed"
    cancelled = "cancelled"


class PickupChannel(str, enum.Enum):
    portal = "portal"
    api = "api"
    phone = "phone"
    manual = "manual"


class PickupRequest(TimestampMixin, Base):
    __tablename__ = "pickup_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    requested_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_pieces: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expected_weight_lbs: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[PickupStatus] = mapped_column(
        Enum(PickupStatus, name="pickup_status"), default=PickupStatus.requested, nullable=False, index=True
    )
    assigned_driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"), nullable=True)
    assigned_tractor_id: Mapped[int | None] = mapped_column(ForeignKey("tractors.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_via: Mapped[PickupChannel] = mapped_column(
        Enum(PickupChannel, name="pickup_channel"), default=PickupChannel.manual, nullable=False
    )


# ── Trips ─────────────────────────────────────────────────
class TripType(str, enum.Enum):
    pickup_delivery = "pickup_delivery"
    linehaul = "linehaul"


class TripStatus(str, enum.Enum):
    planned = "planned"
    dispatched = "dispatched"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class Trip(TimestampMixin, Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    type: Mapped[TripType] = mapped_column(Enum(TripType, name="trip_type"), nullable=False)
    origin_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    destination_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    planned_departure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_arrival_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_departure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_arrival_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tractor_id: Mapped[int | None] = mapped_column(ForeignKey("tractors.id"), nullable=True)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"), nullable=True)
    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus, name="trip_status"), default=TripStatus.planned, nullable=False, index=True
    )


class TrailerPosition(str, enum.Enum):
    lead = "lead"
    pup = "pup"


class TripTrailer(Base):
    __tablename__ = "trip_trailers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False, index=True)
    trailer_id: Mapped[int] = mapped_column(ForeignKey("trailers.id"), nullable=False, index=True)
    position: Mapped[TrailerPosition] = mapped_column(
        Enum(TrailerPosition, name="trailer_position"), default=TrailerPosition.lead, nullable=False
    )
    hooked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dropped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ── Manifests ─────────────────────────────────────────────
class ManifestStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    in_transit = "in_transit"
    arrived = "arrived"
    unloaded = "unloaded"


class Manifest(TimestampMixin, Base):
    __tablename__ = "manifests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trailer_id: Mapped[int] = mapped_column(ForeignKey("trailers.id"), nullable=False, index=True)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id"), nullable=True, index=True)
    origin_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    destination_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    status: Mapped[ManifestStatus] = mapped_column(
        Enum(ManifestStatus, name="manifest_status"), default=ManifestStatus.open, nullable=False, index=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ManifestItem(Base):
    __tablename__ = "manifest_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manifest_id: Mapped[int] = mapped_column(ForeignKey("manifests.id"), nullable=False, index=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), nullable=False, index=True)
    handling_units_loaded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    loaded_by: Mapped[str] = mapped_column(String(120), default="")
    unloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unloaded_by: Mapped[str] = mapped_column(String(120), default="")
