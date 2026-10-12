from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.operations import PickupChannel, PickupStatus


class PickupBase(BaseModel):
    customer_id: int | None = None
    location_id: int | None = None
    requested_date: date | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None
    expected_pieces: int = 0
    expected_weight_lbs: float = 0.0
    assigned_driver_id: int | None = None
    assigned_tractor_id: int | None = None
    notes: str = ""
    created_via: PickupChannel = PickupChannel.manual


class PickupCreate(PickupBase):
    pass


class PickupUpdate(BaseModel):
    location_id: int | None = None
    requested_date: date | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None
    expected_pieces: int | None = None
    expected_weight_lbs: float | None = None
    status: PickupStatus | None = None
    assigned_driver_id: int | None = None
    assigned_tractor_id: int | None = None
    notes: str | None = None


class PickupOut(PickupBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: PickupStatus
