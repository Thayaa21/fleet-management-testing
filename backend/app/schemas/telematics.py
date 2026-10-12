from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.telematics import IngestErrorCode


class PingIn(BaseModel):
    device_serial: str | None = None
    recorded_at: str | None = None
    lat: float | None = None
    lng: float | None = None
    speed_kph: float | None = None
    heading: float | None = None
    odometer_km: float | None = None
    engine_on: bool | None = None


class IngestBatch(BaseModel):
    # Accept loosely-typed pings so malformed ones can be logged, not rejected outright.
    pings: list[dict[str, Any]] = []


class IngestSummary(BaseModel):
    accepted: int
    rejected: int
    by_error: dict[str, int]


class GpsPingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    recorded_at: datetime
    received_at: datetime
    lat: float
    lng: float
    speed_kph: float | None
    heading: float | None


class IngestLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    received_at: datetime
    provider: str
    http_status_returned: int
    device_serial: str | None
    resolved_device_id: int | None
    error_code: IngestErrorCode | None
