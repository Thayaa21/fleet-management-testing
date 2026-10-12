import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class IngestErrorCode(str, enum.Enum):
    UNKNOWN_DEVICE = "UNKNOWN_DEVICE"
    DEVICE_UNASSIGNED = "DEVICE_UNASSIGNED"
    MALFORMED_PAYLOAD = "MALFORMED_PAYLOAD"
    AUTH_FAILED = "AUTH_FAILED"
    DUPLICATE = "DUPLICATE"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GpsPing(Base):
    __tablename__ = "gps_pings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("telematics_devices.id"), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    speed_kph: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    odometer_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    engine_on: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = ()


# Composite index on (device_id, recorded_at)
from sqlalchemy import Index  # noqa: E402

Index("ix_gps_pings_device_recorded", GpsPing.device_id, GpsPing.recorded_at)


class TelematicsIngestLog(Base):
    __tablename__ = "telematics_ingest_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    http_status_returned: Mapped[int] = mapped_column(Integer, nullable=False)
    device_serial: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resolved_device_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[IngestErrorCode | None] = mapped_column(
        Enum(IngestErrorCode, name="ingest_error_code"), nullable=True, index=True
    )
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
