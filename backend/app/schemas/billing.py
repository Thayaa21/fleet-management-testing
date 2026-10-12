from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.billing import (
    DocumentType,
    ExceptionSeverity,
    ExceptionSource,
    ExceptionStatus,
    ExceptionType,
    FreightBillStatus,
)


# ── Documents ──
class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    shipment_id: int
    type: DocumentType
    filename: str
    uploaded_by: str
    uploaded_at: datetime
    source: str


# ── Exceptions ──
class ExceptionCreate(BaseModel):
    shipment_id: int
    type: ExceptionType
    severity: ExceptionSeverity = ExceptionSeverity.medium
    description: str = ""


class ExceptionUpdate(BaseModel):
    status: ExceptionStatus | None = None
    severity: ExceptionSeverity | None = None
    resolution_notes: str | None = None


class ExceptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    shipment_id: int
    type: ExceptionType
    severity: ExceptionSeverity
    status: ExceptionStatus
    description: str
    opened_at: datetime
    opened_by: str
    resolved_at: datetime | None
    resolution_notes: str
    source: ExceptionSource
    dq_code: str | None


# ── Rating / quotes ──
class QuoteRequest(BaseModel):
    origin_terminal_id: int | None = None
    destination_terminal_id: int | None = None
    total_weight_lbs: float
    freight_class: str = "100"
    pickup_date: str | None = None


class QuoteResponse(BaseModel):
    line_items: list[dict]
    subtotal: float
    fuel_surcharge: float
    accessorials_total: float
    total: float


# ── Freight bills ──
class FreightBillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    shipment_id: int
    bill_number: str
    bill_to_customer_id: int | None
    line_items: list
    subtotal: float
    fuel_surcharge: float
    accessorials_total: float
    tax: float
    total: float
    status: FreightBillStatus
    issued_at: datetime | None
