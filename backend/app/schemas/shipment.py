from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.shipment import ServiceLevel, ShipmentSource, ShipmentStatus
from app.schemas.handling_unit import HandlingUnitOut
from app.schemas.milestone import MilestoneOut


class ShipmentBase(BaseModel):
    bol_number: str = ""
    customer_id: int | None = None
    shipper_location_id: int | None = None
    consignee_location_id: int | None = None
    service_level: ServiceLevel = ServiceLevel.standard
    pickup_date: date | None = None
    pickup_window_start: datetime | None = None
    pickup_window_end: datetime | None = None
    delivery_appointment_start: datetime | None = None
    delivery_appointment_end: datetime | None = None
    requested_delivery_date: date | None = None
    total_pieces: int = 0
    total_weight_lbs: float = 0.0
    total_cuft: float = 0.0
    freight_class: str = ""
    nmfc: str | None = None
    hazmat: bool = False
    stackable: bool = False
    is_urgent: bool = False
    po_numbers: list[str] = []
    customer_reference: str = ""
    is_cross_border: bool = False
    customs_broker: str | None = None
    pars_paps_number: str | None = None


class ShipmentCreate(ShipmentBase):
    probill_number: str | None = None  # auto-generated if omitted
    source: ShipmentSource = ShipmentSource.manual


class ShipmentUpdate(BaseModel):
    bol_number: str | None = None
    customer_id: int | None = None
    shipper_location_id: int | None = None
    consignee_location_id: int | None = None
    service_level: ServiceLevel | None = None
    pickup_date: date | None = None
    pickup_window_start: datetime | None = None
    pickup_window_end: datetime | None = None
    delivery_appointment_start: datetime | None = None
    delivery_appointment_end: datetime | None = None
    requested_delivery_date: date | None = None
    total_pieces: int | None = None
    total_weight_lbs: float | None = None
    total_cuft: float | None = None
    freight_class: str | None = None
    nmfc: str | None = None
    hazmat: bool | None = None
    stackable: bool | None = None
    is_urgent: bool | None = None
    po_numbers: list[str] | None = None
    customer_reference: str | None = None
    is_cross_border: bool | None = None
    customs_broker: str | None = None
    pars_paps_number: str | None = None


class ShipmentOut(ShipmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    probill_number: str
    current_status: ShipmentStatus
    current_location_id: int | None
    current_trailer_id: int | None
    current_trip_id: int | None
    estimated_delivery_at: datetime | None
    actual_delivery_at: datetime | None
    data_quality_flags: list
    source: ShipmentSource
    created_by: str
    created_at: datetime
    updated_at: datetime


class ShipmentDetail(ShipmentOut):
    handling_units: list[HandlingUnitOut] = []
    milestones: list[MilestoneOut] = []


class CancelRequest(BaseModel):
    reason: str = ""
