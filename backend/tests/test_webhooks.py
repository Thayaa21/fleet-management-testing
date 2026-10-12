"""Outbound webhooks: enqueue on milestone, delivery, retry/backoff, failing
status, resend, and HMAC signing / no-secret-leak."""
from datetime import datetime, timezone

import pytest

import app.services.webhooks as wh
from app.models.api import ApiClient, WebhookDelivery, WebhookSubscription, WebhookSubStatus
from app.models.customer import Customer, CustomerType
from app.models.milestone import EventCode, MilestoneSource
from app.models.shipment import Shipment
from app.services.shipment_state import add_milestone


@pytest.fixture()
def shipment_with_sub(db_session):
    cust = Customer(account_number="WHCUST", name="WH", type=CustomerType.both)
    db_session.add(cust)
    db_session.flush()
    api_client = ApiClient(customer_id=cust.id, name="WHClient")
    db_session.add(api_client)
    db_session.flush()
    sub = WebhookSubscription(api_client_id=api_client.id, target_url="https://example.test/hook",
                              event_types=["PICKED_UP", "DELIVERED"], secret="s3cr3t")
    db_session.add(sub)
    ship = Shipment(probill_number="PWH1", customer_id=cust.id)
    db_session.add(ship)
    db_session.commit()
    return ship, sub


def test_milestone_enqueues_matching_delivery(db_session, shipment_with_sub):
    ship, sub = shipment_with_sub
    add_milestone(db_session, ship, event_code=EventCode.PICKED_UP, source=MilestoneSource.manual)
    db_session.commit()
    deliveries = db_session.query(WebhookDelivery).filter(WebhookDelivery.subscription_id == sub.id).all()
    assert len(deliveries) == 1
    assert deliveries[0].payload["event"] == "PICKED_UP"


def test_non_matching_event_not_enqueued(db_session, shipment_with_sub):
    ship, sub = shipment_with_sub
    add_milestone(db_session, ship, event_code=EventCode.DEPARTED_TERMINAL, source=MilestoneSource.manual)
    db_session.commit()
    assert db_session.query(WebhookDelivery).count() == 0


def test_delivery_success_signs_payload(db_session, shipment_with_sub, monkeypatch):
    ship, sub = shipment_with_sub
    add_milestone(db_session, ship, event_code=EventCode.PICKED_UP, source=MilestoneSource.manual)
    db_session.commit()

    seen = {}

    def fake_send(url, body, headers):
        seen["url"] = url
        seen["sig"] = headers.get("X-Signature")
        seen["body"] = body
        return 200, "ok"

    monkeypatch.setattr(wh, "send_request", fake_send)
    summary = wh.deliver_pending(db_session)
    assert summary["sent"] == 1
    # Signature is a valid HMAC of the body with the subscription secret.
    assert seen["sig"] == wh.sign("s3cr3t", seen["body"])
    d = db_session.query(WebhookDelivery).first()
    assert d.delivered is True


def test_retry_then_succeed_and_failing_status(db_session, shipment_with_sub, monkeypatch):
    ship, sub = shipment_with_sub
    add_milestone(db_session, ship, event_code=EventCode.PICKED_UP, source=MilestoneSource.manual)
    db_session.commit()

    # First pass: receiver returns 500 → failure recorded, retry scheduled.
    monkeypatch.setattr(wh, "send_request", lambda url, body, headers: (500, "err"))
    wh.deliver_pending(db_session)
    d = db_session.query(WebhookDelivery).first()
    assert d.delivered is False
    assert d.error.value == "HTTP_5XX"
    assert d.next_retry_at is not None
    sub_after = db_session.get(WebhookSubscription, sub.id)
    assert sub_after.consecutive_failures == 1

    # Make it due again and succeed.
    d.next_retry_at = datetime.now(timezone.utc)
    db_session.commit()
    monkeypatch.setattr(wh, "send_request", lambda url, body, headers: (200, "ok"))
    wh.deliver_pending(db_session)
    d2 = db_session.get(WebhookDelivery, d.id)
    assert d2.delivered is True
    assert db_session.get(WebhookSubscription, sub.id).consecutive_failures == 0


def test_five_failures_marks_subscription_failing(db_session, shipment_with_sub, monkeypatch):
    ship, sub = shipment_with_sub
    monkeypatch.setattr(wh, "send_request", lambda url, body, headers: (500, "err"))
    # Enqueue and fail-deliver five times.
    for _ in range(5):
        add_milestone(db_session, ship, event_code=EventCode.PICKED_UP, source=MilestoneSource.manual)
        db_session.commit()
        # Make all pending due now.
        for d in db_session.query(WebhookDelivery).filter(WebhookDelivery.delivered.is_(False)):
            d.next_retry_at = datetime.now(timezone.utc)
        db_session.commit()
        wh.deliver_pending(db_session)
    sub_after = db_session.get(WebhookSubscription, sub.id)
    assert sub_after.status == WebhookSubStatus.failing


def test_resend_marks_undelivered_and_due(db_session, shipment_with_sub, monkeypatch):
    ship, sub = shipment_with_sub
    add_milestone(db_session, ship, event_code=EventCode.PICKED_UP, source=MilestoneSource.manual)
    db_session.commit()
    monkeypatch.setattr(wh, "send_request", lambda url, body, headers: (200, "ok"))
    wh.deliver_pending(db_session)
    d = db_session.query(WebhookDelivery).first()
    assert d.delivered is True
    wh.resend_delivery(db_session, d)
    assert d.delivered is False
    assert d.next_retry_at is not None
