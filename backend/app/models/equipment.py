import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin


# ── Telematics devices ────────────────────────────────────
class TelematicsProvider(str, enum.Enum):
    samsara = "samsara"
    geotab = "geotab"
    mock = "mock"
    other = "other"


class AttachedToType(str, enum.Enum):
    tractor = "tractor"
    trailer = "trailer"
    none = "none"


class DeviceStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    unassigned = "unassigned"


class TelematicsDevice(TimestampMixin, Base):
    __tablename__ = "telematics_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[TelematicsProvider] = mapped_column(
        Enum(TelematicsProvider, name="telematics_provider"), nullable=False
    )
    device_serial: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    attached_to_type: Mapped[AttachedToType] = mapped_column(
        Enum(AttachedToType, name="attached_to_type"), default=AttachedToType.none, nullable=False
    )
    attached_to_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus, name="device_status"), default=DeviceStatus.unassigned, nullable=False
    )
    last_ping_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ── Tractors ──────────────────────────────────────────────
class TractorStatus(str, enum.Enum):
    available = "available"
    in_use = "in_use"
    maintenance = "maintenance"
    out_of_service = "out_of_service"


class Tractor(TimestampMixin, Base):
    __tablename__ = "tractors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    vin: Mapped[str] = mapped_column(String(40), default="")
    plate: Mapped[str] = mapped_column(String(20), default="")
    home_terminal_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    status: Mapped[TractorStatus] = mapped_column(
        Enum(TractorStatus, name="tractor_status"), default=TractorStatus.available, nullable=False
    )
    telematics_device_id: Mapped[int | None] = mapped_column(
        ForeignKey("telematics_devices.id"), nullable=True
    )


# ── Trailers ──────────────────────────────────────────────
class TrailerType(str, enum.Enum):
    dry_van = "dry_van"
    reefer = "reefer"
    flatbed = "flatbed"
    pup = "pup"
    straight_truck_box = "straight_truck_box"


class TrailerStatus(str, enum.Enum):
    available = "available"
    in_use = "in_use"
    maintenance = "maintenance"
    out_of_service = "out_of_service"


class Trailer(TimestampMixin, Base):
    __tablename__ = "trailers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trailer_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    type: Mapped[TrailerType] = mapped_column(Enum(TrailerType, name="trailer_type"), nullable=False)
    length_ft: Mapped[float | None] = mapped_column(Float, nullable=True)
    capacity_lbs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capacity_cuft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_terminal_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    current_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    status: Mapped[TrailerStatus] = mapped_column(
        Enum(TrailerStatus, name="trailer_status"), default=TrailerStatus.available, nullable=False
    )
    telematics_device_id: Mapped[int | None] = mapped_column(
        ForeignKey("telematics_devices.id"), nullable=True
    )
