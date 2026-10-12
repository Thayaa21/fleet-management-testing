import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EventCode(str, enum.Enum):
    PICKUP_REQUESTED = "PICKUP_REQUESTED"
    PICKUP_DISPATCHED = "PICKUP_DISPATCHED"
    ARRIVED_AT_PICKUP = "ARRIVED_AT_PICKUP"
    PICKED_UP = "PICKED_UP"
    ARRIVED_AT_TERMINAL = "ARRIVED_AT_TERMINAL"
    LOADED_ON_TRAILER = "LOADED_ON_TRAILER"
    DEPARTED_TERMINAL = "DEPARTED_TERMINAL"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED_AT_DESTINATION_TERMINAL = "ARRIVED_AT_DESTINATION_TERMINAL"
    UNLOADED = "UNLOADED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    ARRIVED_AT_DELIVERY = "ARRIVED_AT_DELIVERY"
    DELIVERED = "DELIVERED"
    DELIVERY_ATTEMPTED = "DELIVERY_ATTEMPTED"
    APPOINTMENT_SET = "APPOINTMENT_SET"
    DELAYED = "DELAYED"
    EXCEPTION = "EXCEPTION"
    CUSTOMS_HOLD = "CUSTOMS_HOLD"
    CUSTOMS_RELEASED = "CUSTOMS_RELEASED"
    CANCELLED = "CANCELLED"


class MilestoneSource(str, enum.Enum):
    driver_scan = "driver_scan"
    dock_scan = "dock_scan"
    telematics = "telematics"
    manual = "manual"
    api = "api"
    edi = "edi"
    agent = "agent"
    system = "system"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Milestone(Base):
    """Append-only status event. Corrections are made by voiding + adding, never
    by editing in place."""

    __tablename__ = "milestones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), nullable=False, index=True)
    event_code: Mapped[EventCode] = mapped_column(Enum(EventCode, name="event_code"), nullable=False)

    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    trailer_id: Mapped[int | None] = mapped_column(ForeignKey("trailers.id"), nullable=True)
    tractor_id: Mapped[int | None] = mapped_column(ForeignKey("tractors.id"), nullable=True)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"), nullable=True)

    source: Mapped[MilestoneSource] = mapped_column(Enum(MilestoneSource, name="milestone_source"), nullable=False)
    edi_214_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[str] = mapped_column(String(120), default="")

    is_voided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    voided_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
