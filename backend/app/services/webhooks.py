"""Outbound webhooks: enqueue on milestone, HMAC-sign, deliver with retries.

`send_request` is a module-level function tests monkeypatch. Backoff schedule for
consecutive attempts: 1m, 5m, 30m, 2h, 6h; after 5 consecutive failures a
subscription is marked `failing`.
"""
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api import (
    ApiClient,
    WebhookDelivery,
    WebhookError,
    WebhookSubscription,
    WebhookSubStatus,
)
from app.models.milestone import Milestone
from app.models.shipment import Shipment

BACKOFF_MINUTES = [1, 5, 30, 120, 360]
MAX_CONSECUTIVE_FAILURES = 5
TIMEOUT_S = 5.0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt):
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def sign(secret: str, body: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


def send_request(url: str, body: str, headers: dict) -> tuple[int, str]:
    """POST the webhook. Returns (status_code, body_snippet). Raises on transport
    errors (caught by the caller and classified). Monkeypatched in tests."""
    import httpx

    resp = httpx.post(url, content=body, headers=headers, timeout=TIMEOUT_S)
    return resp.status_code, resp.text[:500]


def _milestone_payload(shipment: Shipment, milestone: Milestone) -> dict:
    return {
        "event": milestone.event_code.value,
        "probill_number": shipment.probill_number,
        "shipment_id": shipment.id,
        "occurred_at": (_aware(milestone.event_at).isoformat() if milestone.event_at else None),
        "milestone": {
            "event_code": milestone.event_code.value,
            "event_at": _aware(milestone.event_at).isoformat() if milestone.event_at else None,
            "source": milestone.source.value,
            "edi_214_code": milestone.edi_214_code,
        },
    }


def enqueue_deliveries(db: Session, shipment: Shipment, milestone: Milestone) -> int:
    """Queue a delivery per active subscription of the shipment's customer whose
    event_types include this milestone's code. Returns count."""
    if shipment.customer_id is None:
        return 0
    client_ids = [c.id for c in db.scalars(select(ApiClient).where(ApiClient.customer_id == shipment.customer_id))]
    if not client_ids:
        return 0
    subs = db.scalars(
        select(WebhookSubscription).where(
            WebhookSubscription.api_client_id.in_(client_ids),
            WebhookSubscription.status != WebhookSubStatus.paused,
        )
    ).all()
    payload = _milestone_payload(shipment, milestone)
    count = 0
    for sub in subs:
        if sub.event_types and milestone.event_code.value not in sub.event_types:
            continue
        db.add(WebhookDelivery(
            subscription_id=sub.id, shipment_id=shipment.id, milestone_id=milestone.id,
            payload=payload, attempt_number=1, next_retry_at=_now(), delivered=False,
        ))
        count += 1
    return count


def _classify(status: int) -> WebhookError | None:
    if 200 <= status < 300:
        return None
    if status in (401, 403):
        return WebhookError.AUTH_REJECTED
    if 400 <= status < 500:
        return WebhookError.HTTP_4XX
    return WebhookError.HTTP_5XX


def deliver_pending(db: Session, limit: int = 50) -> dict:
    """Attempt all due, undelivered deliveries. Returns a small summary."""
    now = _now()
    due = db.scalars(
        select(WebhookDelivery).where(
            WebhookDelivery.delivered.is_(False),
            WebhookDelivery.next_retry_at <= now,
        ).limit(limit)
    ).all()

    sent, failed = 0, 0
    for d in due:
        sub = db.get(WebhookSubscription, d.subscription_id)
        if sub is None or sub.status == WebhookSubStatus.paused:
            continue
        body = json.dumps(d.payload, separators=(",", ":"), sort_keys=True)
        headers = {"Content-Type": "application/json", "X-Signature": sign(sub.secret or "", body)}
        d.sent_at = _now()
        try:
            status, snippet = send_request(sub.target_url, body, headers)
            d.response_status = status
            d.response_body_snippet = snippet
            err = _classify(status)
        except TimeoutError:
            status, err, d.response_body_snippet = 0, WebhookError.TIMEOUT, "timeout"
        except Exception as exc:  # noqa: BLE001 — transport errors classified generically
            status, err, d.response_body_snippet = 0, WebhookError.CONNECTION_ERROR, str(exc)[:200]

        if err is None:
            d.delivered = True
            d.error = None
            sub.consecutive_failures = 0
            if sub.status == WebhookSubStatus.failing:
                sub.status = WebhookSubStatus.active
            sent += 1
        else:
            d.error = err
            sub.consecutive_failures = (sub.consecutive_failures or 0) + 1
            idx = min(d.attempt_number - 1, len(BACKOFF_MINUTES) - 1)
            d.next_retry_at = _now() + timedelta(minutes=BACKOFF_MINUTES[idx])
            d.attempt_number += 1
            if sub.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                sub.status = WebhookSubStatus.failing
            failed += 1

    db.commit()
    return {"sent": sent, "failed": failed, "attempted": len(due)}


def resend_delivery(db: Session, delivery: WebhookDelivery) -> None:
    delivery.delivered = False
    delivery.next_retry_at = _now()
    db.commit()
