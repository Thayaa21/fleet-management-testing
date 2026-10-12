from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.audit import AuditLog
from app.schemas.audit import AuditOut
from app.schemas.common import Page
from app.services.auth import require_staff
from app.services.crud import clamp_page, paginate

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(require_staff)])


@router.get("", response_model=Page[AuditOut])
def list_audit(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    entity_type: str | None = None,
    entity_id: int | None = None,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(AuditLog)
    if entity_type is not None:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    stmt = stmt.order_by(AuditLog.created_at.desc())
    items, total = paginate(db, stmt, p, ps)
    return Page[AuditOut](items=items, total=total, page=p, page_size=ps)
