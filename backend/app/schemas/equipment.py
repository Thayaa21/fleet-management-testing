from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.equipment import (
    AttachedToType,
    DeviceStatus,
    TelematicsProvider,
    TractorStatus,
    TrailerStatus,
    TrailerType,
)


def _upper(v: str | None) -> str | None:
    return v.strip().upper() if isinstance(v, str) else v


# ── Telematics devices ────────────────────────────────────
class DeviceBase(BaseModel):
    provider: TelematicsProvider
    installed_at: datetime | None = None


class DeviceCreate(DeviceBase):
    device_serial: str

    @field_validator("device_serial")
    @classmethod
    def norm_serial(cls, v: str) -> str:
        return _upper(v)


class DeviceUpdate(BaseModel):
    provider: TelematicsProvider | None = None
    device_serial: str | None = None
    status: DeviceStatus | None = None
    installed_at: datetime | None = None

    @field_validator("device_serial")
    @classmethod
    def norm_serial(cls, v: str | None) -> str | None:
        return _upper(v)


class DeviceOut(DeviceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_serial: str
    attached_to_type: AttachedToType
    attached_to_id: int | None
    status: DeviceStatus
    last_ping_at: datetime | None


# ── Tractors ──────────────────────────────────────────────
class TractorBase(BaseModel):
    vin: str = ""
    plate: str = ""
    home_terminal_id: int | None = None
    telematics_device_id: int | None = None


class TractorCreate(TractorBase):
    unit_number: str

    @field_validator("unit_number")
    @classmethod
    def norm_unit(cls, v: str) -> str:
        return _upper(v)


class TractorUpdate(BaseModel):
    unit_number: str | None = None
    vin: str | None = None
    plate: str | None = None
    home_terminal_id: int | None = None
    status: TractorStatus | None = None
    telematics_device_id: int | None = None

    @field_validator("unit_number")
    @classmethod
    def norm_unit(cls, v: str | None) -> str | None:
        return _upper(v)


class TractorOut(TractorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unit_number: str
    status: TractorStatus


# ── Trailers ──────────────────────────────────────────────
class TrailerBase(BaseModel):
    type: TrailerType
    length_ft: float | None = None
    capacity_lbs: int | None = None
    capacity_cuft: int | None = None
    home_terminal_id: int | None = None
    current_location_id: int | None = None
    telematics_device_id: int | None = None


class TrailerCreate(TrailerBase):
    trailer_number: str

    @field_validator("trailer_number")
    @classmethod
    def norm_num(cls, v: str) -> str:
        return _upper(v)


class TrailerUpdate(BaseModel):
    trailer_number: str | None = None
    type: TrailerType | None = None
    length_ft: float | None = None
    capacity_lbs: int | None = None
    capacity_cuft: int | None = None
    home_terminal_id: int | None = None
    current_location_id: int | None = None
    status: TrailerStatus | None = None
    telematics_device_id: int | None = None

    @field_validator("trailer_number")
    @classmethod
    def norm_num(cls, v: str | None) -> str | None:
        return _upper(v)


class TrailerOut(TrailerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trailer_number: str
    status: TrailerStatus
