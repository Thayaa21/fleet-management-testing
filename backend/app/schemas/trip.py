from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.operations import TrailerPosition, TripStatus, TripType


def _upper(v):
    return v.strip().upper() if isinstance(v, str) else v


class TripBase(BaseModel):
    type: TripType
    origin_location_id: int | None = None
    destination_location_id: int | None = None
    planned_departure_at: datetime | None = None
    planned_arrival_at: datetime | None = None
    tractor_id: int | None = None
    driver_id: int | None = None


class TripCreate(TripBase):
    trip_number: str | None = None  # auto-generated if omitted

    @field_validator("trip_number")
    @classmethod
    def norm(cls, v):
        return _upper(v)


class TripUpdate(BaseModel):
    origin_location_id: int | None = None
    destination_location_id: int | None = None
    planned_departure_at: datetime | None = None
    planned_arrival_at: datetime | None = None
    tractor_id: int | None = None
    driver_id: int | None = None
    status: TripStatus | None = None


class TripOut(TripBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_number: str
    status: TripStatus
    actual_departure_at: datetime | None
    actual_arrival_at: datetime | None


class HookTrailerRequest(BaseModel):
    trailer_number: str
    position: TrailerPosition = TrailerPosition.lead
