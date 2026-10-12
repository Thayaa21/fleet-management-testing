from pydantic import BaseModel, ConfigDict

from app.models.location import LocationStatus, LocationType


class LocationBase(BaseModel):
    customer_id: int | None = None
    name: str
    type: LocationType
    address: str = ""
    city: str = ""
    province_state: str = ""
    postal_zip: str = ""
    country: str = ""
    lat: float | None = None
    lng: float | None = None
    timezone: str = ""
    dock_hours: str = ""
    appointment_required: bool = False
    geofence_radius_m: int = 300


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    customer_id: int | None = None
    name: str | None = None
    type: LocationType | None = None
    address: str | None = None
    city: str | None = None
    province_state: str | None = None
    postal_zip: str | None = None
    country: str | None = None
    lat: float | None = None
    lng: float | None = None
    timezone: str | None = None
    dock_hours: str | None = None
    appointment_required: bool | None = None
    geofence_radius_m: int | None = None
    status: LocationStatus | None = None


class LocationOut(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: LocationStatus
