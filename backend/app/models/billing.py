import enum
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Documents ─────────────────────────────────────────────
class DocumentType(str, enum.Enum):
    BOL = "BOL"
    POD = "POD"
    customs = "customs"
    photo = "photo"
    other = "other"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), nullable=False, index=True)
    type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, name="document_type"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String(120), default="")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="manual")


# ── Exceptions (OS&D) ─────────────────────────────────────
class ExceptionType(str, enum.Enum):
    overage = "overage"
    shortage = "shortage"
    damage = "damage"
    refused = "refused"
    missed_pickup = "missed_pickup"
    missed_delivery = "missed_delivery"
    delay = "delay"
    customs_hold = "customs_hold"
    data_quality = "data_quality"


class ExceptionSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ExceptionStatus(str, enum.Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"


class ExceptionSource(str, enum.Enum):
    user = "user"
    system = "system"
    agent = "agent"


class Exception_(TimestampMixin, Base):
    __tablename__ = "exceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), nullable=False, index=True)
    type: Mapped[ExceptionType] = mapped_column(Enum(ExceptionType, name="exception_type"), nullable=False, index=True)
    severity: Mapped[ExceptionSeverity] = mapped_column(
        Enum(ExceptionSeverity, name="exception_severity"), default=ExceptionSeverity.medium, nullable=False, index=True
    )
    status: Mapped[ExceptionStatus] = mapped_column(
        Enum(ExceptionStatus, name="exception_status"), default=ExceptionStatus.open, nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, default="")
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    opened_by: Mapped[str] = mapped_column(String(120), default="")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str] = mapped_column(String(120), default="")
    resolution_notes: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[ExceptionSource] = mapped_column(
        Enum(ExceptionSource, name="exception_source"), default=ExceptionSource.system, nullable=False
    )
    # Quick-filter key for data-quality flags this exception was derived from.
    dq_code: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)


# ── Rating ────────────────────────────────────────────────
class RateTable(Base):
    """Rate per hundredweight (cwt) for a lane + weight break + freight class."""
    __tablename__ = "rate_tables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    origin_terminal_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True, index=True)
    destination_terminal_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True, index=True)
    weight_break_min: Mapped[float] = mapped_column(Float, default=0, nullable=False)   # inclusive lbs
    weight_break_max: Mapped[float | None] = mapped_column(Float, nullable=True)          # exclusive; null = no upper
    freight_class: Mapped[str] = mapped_column(String(10), nullable=False)
    rate_per_cwt: Mapped[float] = mapped_column(Float, nullable=False)
    minimum_charge: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)


class FuelSurcharge(Base):
    __tablename__ = "fuel_surcharge"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    percent: Mapped[float] = mapped_column(Float, nullable=False)  # e.g. 20.0 == 20%


class Accessorial(Base):
    __tablename__ = "accessorials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    charge: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    per_hour: Mapped[bool] = mapped_column(Integer, default=0)  # 0/1; detention is per hour


class ShipmentAccessorial(Base):
    __tablename__ = "shipment_accessorials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), nullable=False, index=True)
    accessorial_id: Mapped[int] = mapped_column(ForeignKey("accessorials.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # hours for per-hour items


# ── Freight bills ─────────────────────────────────────────
class FreightBillStatus(str, enum.Enum):
    draft = "draft"
    issued = "issued"
    paid = "paid"
    void = "void"


class FreightBill(TimestampMixin, Base):
    __tablename__ = "freight_bills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), nullable=False, index=True)
    bill_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    bill_to_customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    line_items: Mapped[list] = mapped_column(JSON, default=list)
    subtotal: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    fuel_surcharge: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    accessorials_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tax: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[FreightBillStatus] = mapped_column(
        Enum(FreightBillStatus, name="freight_bill_status"), default=FreightBillStatus.draft, nullable=False, index=True
    )
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
