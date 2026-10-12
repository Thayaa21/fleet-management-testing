from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.milestone import EventCode, MilestoneSource


class MilestoneCreate(BaseModel):
    event_code: EventCode
    source: MilestoneSource = MilestoneSource.manual
    event_at: datetime | None = None
    location_id: int | None = None
    lat: float | None = None
    lng: float | None = None
    trailer_id: int | None = None
    tractor_id: int | None = None
    driver_id: int | None = None
    edi_214_code: str | None = None
    notes: str = ""


class MilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int
    event_code: EventCode
    event_at: datetime
    recorded_at: datetime
    location_id: int | None
    lat: float | None
    lng: float | None
    trailer_id: int | None
    tractor_id: int | None
    driver_id: int | None
    source: MilestoneSource
    edi_214_code: str | None
    notes: str
    created_by: str
    is_voided: bool
    voided_reason: str | None


class VoidRequest(BaseModel):
    reason: str
