from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.api import (
    ApiClient,
    ApiErrorCode,
    ApiKey,
    ApiRequestLog,
    IpAllowlist,
    WebhookDelivery,
    WebhookSubscription,
)
from app.models.customer import Customer
from app.schemas.common import Page
from app.schemas.integrations import (
    ApiClientCreate,
    ApiClientOut,
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyOut,
    ApiLogOut,
    IpAllowlistCreate,
    IpAllowlistOut,
    WebhookDeliveryOut,
    WebhookSubCreate,
    WebhookSubOut,
)
from app.services.api_keys import create_api_key
from app.services.auth import require_staff
from app.services.crud import clamp_page, paginate
from app.services.refs import ensure_exists
from app.services.webhooks import resend_delivery

router = APIRouter(prefix="/integrations", tags=["integrations"], dependencies=[Depends(require_staff)])


# ── API clients ──
@router.get("/clients", response_model=list[ApiClientOut])
def list_clients(db: Session = Depends(get_db)):
    return list(db.scalars(select(ApiClient).order_by(ApiClient.name)))


@router.post("/clients", response_model=ApiClientOut, status_code=201)
def create_client(body: ApiClientCreate, db: Session = Depends(get_db)):
    ensure_exists(db, Customer, body.customer_id, "customer_id")
    obj = ApiClient(customer_id=body.customer_id, name=body.name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── Keys ──
@router.get("/clients/{client_id}/keys", response_model=list[ApiKeyOut])
def list_keys(client_id: int, db: Session = Depends(get_db)):
    return list(db.scalars(select(ApiKey).where(ApiKey.api_client_id == client_id)))


@router.post("/clients/{client_id}/keys", response_model=ApiKeyCreated, status_code=201)
def create_key(client_id: int, body: ApiKeyCreate, db: Session = Depends(get_db)):
    if db.get(ApiClient, client_id) is None:
        raise APIError(404, "NOT_FOUND", "API client not found.")
    row, full = create_api_key(db, client_id, body.scopes, body.expires_at)
    db.commit()
    db.refresh(row)
    out = ApiKeyOut.model_validate(row).model_dump()
    out["api_key"] = full  # shown ONCE
    return out


@router.post("/keys/{key_id}/revoke", response_model=ApiKeyOut)
def revoke_key(key_id: int, db: Session = Depends(get_db)):
    key = db.get(ApiKey, key_id)
    if key is None:
        raise APIError(404, "NOT_FOUND", "API key not found.")
    key.revoked_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(key)
    return key


# ── IP allowlist ──
@router.get("/clients/{client_id}/allowlist", response_model=list[IpAllowlistOut])
def list_allowlist(client_id: int, db: Session = Depends(get_db)):
    return list(db.scalars(select(IpAllowlist).where(IpAllowlist.api_client_id == client_id)))


@router.post("/clients/{client_id}/allowlist", response_model=IpAllowlistOut, status_code=201)
def add_allowlist(client_id: int, body: IpAllowlistCreate, db: Session = Depends(get_db)):
    if db.get(ApiClient, client_id) is None:
        raise APIError(404, "NOT_FOUND", "API client not found.")
    obj = IpAllowlist(api_client_id=client_id, cidr=body.cidr, label=body.label)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/allowlist/{entry_id}", status_code=204)
def delete_allowlist(entry_id: int, db: Session = Depends(get_db)):
    obj = db.get(IpAllowlist, entry_id)
    if obj is not None:
        db.delete(obj)
        db.commit()


# ── Webhook subscriptions ──
@router.get("/clients/{client_id}/subscriptions", response_model=list[WebhookSubOut])
def list_subs(client_id: int, db: Session = Depends(get_db)):
    return list(db.scalars(select(WebhookSubscription).where(WebhookSubscription.api_client_id == client_id)))


@router.post("/clients/{client_id}/subscriptions", response_model=WebhookSubOut, status_code=201)
def create_sub(client_id: int, body: WebhookSubCreate, db: Session = Depends(get_db)):
    if db.get(ApiClient, client_id) is None:
        raise APIError(404, "NOT_FOUND", "API client not found.")
    obj = WebhookSubscription(api_client_id=client_id, target_url=body.target_url,
                              event_types=body.event_types, secret=body.secret)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# ── API request log ──
@router.get("/api-logs", response_model=Page[ApiLogOut])
def api_logs(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    api_client_id: int | None = None,
    error_code: ApiErrorCode | None = None,
    status: int | None = None,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(ApiRequestLog)
    if api_client_id is not None:
        stmt = stmt.where(ApiRequestLog.api_client_id == api_client_id)
    if error_code is not None:
        stmt = stmt.where(ApiRequestLog.error_code == error_code)
    if status is not None:
        stmt = stmt.where(ApiRequestLog.response_status == status)
    stmt = stmt.order_by(ApiRequestLog.received_at.desc())
    items, total = paginate(db, stmt, p, ps)
    return Page[ApiLogOut](items=items, total=total, page=p, page_size=ps)


# ── Webhook deliveries ──
@router.get("/webhook-deliveries", response_model=Page[WebhookDeliveryOut])
def webhook_deliveries(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    delivered: bool | None = None,
    subscription_id: int | None = None,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(WebhookDelivery)
    if delivered is not None:
        stmt = stmt.where(WebhookDelivery.delivered == delivered)
    if subscription_id is not None:
        stmt = stmt.where(WebhookDelivery.subscription_id == subscription_id)
    stmt = stmt.order_by(WebhookDelivery.created_at.desc())
    items, total = paginate(db, stmt, p, ps)
    return Page[WebhookDeliveryOut](items=items, total=total, page=p, page_size=ps)


@router.post("/webhook-deliveries/{delivery_id}/resend", response_model=WebhookDeliveryOut)
def resend(delivery_id: int, db: Session = Depends(get_db)):
    d = db.get(WebhookDelivery, delivery_id)
    if d is None:
        raise APIError(404, "NOT_FOUND", "Delivery not found.")
    resend_delivery(db, d)
    db.refresh(d)
    return d


@router.post("/webhook-deliveries/deliver-now")
def deliver_now(db: Session = Depends(get_db)):
    """Manually trigger a delivery pass (dev/ops convenience)."""
    from app.services.webhooks import deliver_pending
    return deliver_pending(db)
