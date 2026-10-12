from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models.equipment import AttachedToType, TelematicsDevice, Tractor
from app.models.operations import Trip, TripStatus
from app.models.telematics import IngestErrorCode, TelematicsIngestLog
from app.schemas.common import Page
from app.schemas.telematics import IngestBatch, IngestLogOut, IngestSummary
from app.services.auth import require_staff
from app.services.crud import clamp_page, paginate
from app.services.telematics import ingest_batch

settings = get_settings()

# Machine-facing ingest endpoint (secured by shared secret, not user auth).
ingest_router = APIRouter(prefix="/integrations/telematics", tags=["telematics-ingest"])
# Staff-facing views.
router = APIRouter(prefix="/telematics", tags=["telematics"], dependencies=[Depends(require_staff)])
logs_router = APIRouter(prefix="/integrations/telematics", tags=["telematics"], dependencies=[Depends(require_staff)])


@ingest_router.post("/{provider}/webhook", response_model=IngestSummary)
def webhook(
    provider: str,
    body: IngestBatch,
    db: Session = Depends(get_db),
    x_telematics_secret: str | None = Header(default=None),
):
    summary = ingest_batch(db, provider, x_telematics_secret, body.pings)
    return IngestSummary(**summary)


@logs_router.get("/logs", response_model=Page[IngestLogOut])
def ingest_logs(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    provider: str | None = None,
    error_code: IngestErrorCode | None = None,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(TelematicsIngestLog)
    if provider is not None:
        stmt = stmt.where(TelematicsIngestLog.provider == provider.lower())
    if error_code is not None:
        stmt = stmt.where(TelematicsIngestLog.error_code == error_code)
    stmt = stmt.order_by(TelematicsIngestLog.received_at.desc())
    items, total = paginate(db, stmt, p, ps)
    return Page[IngestLogOut](items=items, total=total, page=p, page_size=ps)


@router.get("/health")
def telematics_health(db: Session = Depends(get_db), hours: int | None = None):
    """Devices with no ping in N hours while their tractor is on an in-progress trip."""
    hours = hours or settings.telematics_stale_hours
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    stale = []
    in_progress_tractor_ids = {
        t.tractor_id for t in db.scalars(select(Trip).where(Trip.status == TripStatus.in_progress))
        if t.tractor_id is not None
    }
    for device in db.scalars(select(TelematicsDevice).where(TelematicsDevice.attached_to_type == AttachedToType.tractor)):
        if device.attached_to_id not in in_progress_tractor_ids:
            continue
        last = device.last_ping_at
        if last is not None and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last is None or last < cutoff:
            tractor = db.get(Tractor, device.attached_to_id)
            stale.append({
                "device_id": device.id, "device_serial": device.device_serial,
                "tractor_id": device.attached_to_id,
                "tractor_unit": tractor.unit_number if tractor else None,
                "last_ping_at": last.isoformat() if last else None,
            })
    return {"hours": hours, "stale_devices": stale}
