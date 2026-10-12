from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.billing import (
    Exception_,
    ExceptionSeverity,
    ExceptionSource,
    ExceptionStatus,
    ExceptionType,
)
from app.models.shipment import Shipment
from app.models.user import User
from app.schemas.billing import ExceptionCreate, ExceptionOut, ExceptionUpdate
from app.schemas.common import Page
from app.services.auth import get_current_user, require_staff
from app.services.crud import clamp_page, paginate
from app.services.exceptions import open_exception, resolve_exception

router = APIRouter(prefix="/exceptions", tags=["exceptions"], dependencies=[Depends(require_staff)])


@router.get("", response_model=Page[ExceptionOut])
def list_exceptions(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: ExceptionType | None = None,
    severity: ExceptionSeverity | None = None,
    status: ExceptionStatus | None = None,
    source: ExceptionSource | None = None,
    shipment_id: int | None = None,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(Exception_)
    if type is not None:
        stmt = stmt.where(Exception_.type == type)
    if severity is not None:
        stmt = stmt.where(Exception_.severity == severity)
    if status is not None:
        stmt = stmt.where(Exception_.status == status)
    if source is not None:
        stmt = stmt.where(Exception_.source == source)
    if shipment_id is not None:
        stmt = stmt.where(Exception_.shipment_id == shipment_id)
    stmt = stmt.order_by(Exception_.opened_at.desc())
    items, total = paginate(db, stmt, p, ps)
    return Page[ExceptionOut](items=items, total=total, page=p, page_size=ps)


@router.post("", response_model=ExceptionOut, status_code=201)
def create_exception(body: ExceptionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.get(Shipment, body.shipment_id) is None:
        raise APIError(404, "NOT_FOUND", "Shipment not found.")
    exc = open_exception(db, body.shipment_id, type_=body.type, severity=body.severity,
                         description=body.description, source=ExceptionSource.user, opened_by=user.email)
    db.commit()
    db.refresh(exc)
    return exc


@router.patch("/{exception_id}", response_model=ExceptionOut)
def update_exception(exception_id: int, body: ExceptionUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    exc = db.get(Exception_, exception_id)
    if exc is None:
        raise APIError(404, "NOT_FOUND", "Exception not found.")
    data = body.model_dump(exclude_unset=True)
    if data.get("status") == ExceptionStatus.resolved:
        resolve_exception(db, exc, data.get("resolution_notes", ""), user.email)
    else:
        for k, v in data.items():
            setattr(exc, k, v)
    db.commit()
    db.refresh(exc)
    return exc
