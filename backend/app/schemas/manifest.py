from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.operations import ManifestStatus


class ManifestCreate(BaseModel):
    trailer_number: str
    trip_id: int | None = None
    origin_location_id: int | None = None
    destination_location_id: int | None = None


class ManifestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trailer_id: int
    trip_id: int | None
    origin_location_id: int | None
    destination_location_id: int | None
    status: ManifestStatus
    closed_at: datetime | None


class LoadRequest(BaseModel):
    trailer_number: str | None = None
    shipment_id: int | None = None
    probill_number: str | None = None
    handling_units_loaded: int = 0

    @model_validator(mode="after")
    def _need_a_shipment(self):
        if self.shipment_id is None and not self.probill_number:
            raise ValueError("Provide shipment_id or probill_number.")
        return self


class UnloadRequest(BaseModel):
    shipment_id: int | None = None
    probill_number: str | None = None

    @model_validator(mode="after")
    def _need_a_shipment(self):
        if self.shipment_id is None and not self.probill_number:
            raise ValueError("Provide shipment_id or probill_number.")
        return self


class ManifestItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    manifest_id: int
    shipment_id: int
    handling_units_loaded: int
    loaded_at: datetime | None
    loaded_by: str
    unloaded_at: datetime | None
    unloaded_by: str
