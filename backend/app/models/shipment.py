import enum
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin


class ShipmentStatus(str, enum.Enum):
    BOOKED = "BOOKED"
    PICKUP_DISPATCHED = "PICKUP_DISPATCHED"
    PICKED_UP = "PICKED_UP"
    AT_ORIGIN_TERMINAL = "AT_ORIGIN_TERMINAL"
    IN_LINEHAUL = "IN_LINEHAUL"
    AT_DESTINATION_TERMINAL = "AT_DESTINATION_TERMINAL"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    EXCEPTION = "EXCEPTION"
    CANCELLED = "CANCELLED"


class ServiceLevel(str, enum.Enum):
    standard = "standard"
    guaranteed = "guaranteed"
    expedited = "expedited"


class ShipmentSource(str, enum.Enum):
    portal = "portal"
    api = "api"
    edi = "edi"
    manual = "manual"
    import_ = "import"


class HandlingUnitType(str, enum.Enum):
    skid = "skid"
    pallet = "pallet"
    crate = "crate"
    loose = "loose"


class Shipment(TimestampMixin, Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    probill_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    bol_number: Mapped[str] = mapped_column(String(50), default="")

    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    shipper_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    consignee_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)

    service_level: Mapped[ServiceLevel] = mapped_column(
        Enum(ServiceLevel, name="service_level"), default=ServiceLevel.standard, nullable=False
    )
    pickup_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    pickup_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pickup_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_appointment_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_appointment_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requested_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    total_pieces: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_weight_lbs: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_cuft: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    freight_class: Mapped[str] = mapped_column(String(10), default="")  # 50..500
    nmfc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    hazmat: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stackable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    po_numbers: Mapped[list] = mapped_column(JSON, default=list)
    customer_reference: Mapped[str] = mapped_column(String(120), default="")

    is_cross_border: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    customs_broker: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pars_paps_number: Mapped[str | None] = mapped_column(String(60), nullable=True)

    current_status: Mapped[ShipmentStatus] = mapped_column(
        Enum(ShipmentStatus, name="shipment_status"), default=ShipmentStatus.BOOKED, nullable=False, index=True
    )
    current_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    current_trailer_id: Mapped[int | None] = mapped_column(ForeignKey("trailers.id"), nullable=True)
    current_trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id"), nullable=True)

    data_quality_flags: Mapped[list] = mapped_column(JSON, default=list)

    # Snapshot of the rated total at booking (Batch 8 rating).
    rated_total: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_by: Mapped[str] = mapped_column(String(120), default="")
    source: Mapped[ShipmentSource] = mapped_column(
        Enum(ShipmentSource, name="shipment_source"), default=ShipmentSource.manual, nullable=False
    )


class HandlingUnit(TimestampMixin, Base):
    __tablename__ = "handling_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), nullable=False, index=True)
    type: Mapped[HandlingUnitType] = mapped_column(
        Enum(HandlingUnitType, name="handling_unit_type"), default=HandlingUnitType.skid, nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    length_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    width_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_in: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_lbs: Mapped[float | None] = mapped_column(Float, nullable=True)
    stackable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    label_barcode: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True, index=True)
