from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.billing import (
    Document,
    DocumentType,
    ExceptionSeverity,
    ExceptionSource,
    ExceptionType,
    FreightBill,
    FreightBillStatus,
)
from app.models.shipment import Shipment, ShipmentStatus
from app.models.user import User
from app.schemas.billing import (
    DocumentOut,
    FreightBillOut,
    QuoteRequest,
    QuoteResponse,
)
from app.schemas.common import Page
from app.services.auth import get_current_user, require_staff
from app.services.billing import issue_bill
from app.services.crud import clamp_page, paginate
from app.services.exceptions import open_exception
from app.services.rating import rate_shipment
from app.services.storage import storage

router = APIRouter(tags=["billing"], dependencies=[Depends(require_staff)])


# ── Quotes ──
@router.post("/quotes", response_model=QuoteResponse)
def quote(body: QuoteRequest, db: Session = Depends(get_db)):
    # Build a throwaway shipment-like object to reuse the rating engine.
    from datetime import date
    stub = Shipment(
        probill_number="__quote__",
        shipper_location_id=body.origin_terminal_id,
        consignee_location_id=body.destination_terminal_id,
        total_weight_lbs=body.total_weight_lbs,
        freight_class=body.freight_class,
        pickup_date=date.fromisoformat(body.pickup_date) if body.pickup_date else None,
    )
    # Give it an id-less identity; rate_shipment only reads fields + queries by id
    # for accessorials (none for a quote), so a transient object is fine.
    stub.id = -1
    return QuoteResponse(**rate_shipment(db, stub))


# ── Documents ──
@router.get("/shipments/{shipment_id}/documents", response_model=list[DocumentOut])
def list_documents(shipment_id: int, db: Session = Depends(get_db)):
    if db.get(Shipment, shipment_id) is None:
        raise APIError(404, "NOT_FOUND", "Shipment not found.")
    return list(db.scalars(select(Document).where(Document.shipment_id == shipment_id)))


@router.post("/shipments/{shipment_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    shipment_id: int,
    type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    shipment = db.get(Shipment, shipment_id)
    if shipment is None:
        raise APIError(404, "NOT_FOUND", "Shipment not found.")

    data = await file.read()
    path = storage.save(shipment_id, file.filename or "upload.bin", data)
    doc = Document(shipment_id=shipment_id, type=type, filename=file.filename or "upload.bin",
                   storage_path=path, uploaded_by=user.email, source="manual")
    db.add(doc)

    # A POD uploaded before the shipment is DELIVERED is a data-quality signal.
    if type == DocumentType.POD and shipment.current_status != ShipmentStatus.DELIVERED:
        flags = list(shipment.data_quality_flags or [])
        flags.append({"code": "POD_WITHOUT_DELIVERY",
                      "detail": f"POD uploaded while status is {shipment.current_status.value}"})
        shipment.data_quality_flags = flags
        open_exception(db, shipment_id, type_=ExceptionType.data_quality, severity=ExceptionSeverity.medium,
                       description="POD uploaded before a DELIVERED milestone.",
                       source=ExceptionSource.system, dq_code="POD_WITHOUT_DELIVERY")

    db.commit()
    db.refresh(doc)
    return doc


# ── Freight bills ──
@router.get("/freight-bills", response_model=Page[FreightBillOut])
def list_bills(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: FreightBillStatus | None = None,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(FreightBill)
    if status is not None:
        stmt = stmt.where(FreightBill.status == status)
    stmt = stmt.order_by(FreightBill.created_at.desc())
    items, total = paginate(db, stmt, p, ps)
    return Page[FreightBillOut](items=items, total=total, page=p, page_size=ps)


@router.get("/freight-bills/{bill_id}", response_model=FreightBillOut)
def get_bill(bill_id: int, db: Session = Depends(get_db)):
    bill = db.get(FreightBill, bill_id)
    if bill is None:
        raise APIError(404, "NOT_FOUND", "Freight bill not found.")
    return bill


@router.post("/freight-bills/{bill_id}/issue", response_model=FreightBillOut)
def issue(bill_id: int, db: Session = Depends(get_db)):
    bill = db.get(FreightBill, bill_id)
    if bill is None:
        raise APIError(404, "NOT_FOUND", "Freight bill not found.")
    if bill.status != FreightBillStatus.draft:
        raise APIError(409, "INVALID_STATE", "Only draft bills can be issued.")
    issue_bill(db, bill)
    db.commit()
    db.refresh(bill)
    return bill
