"""Rating, exceptions (incl. DQ-flag conversion), freight bills, and the
POD-without-delivery signal."""
from datetime import date

import pytest

from app.models.billing import Accessorial, FuelSurcharge, RateTable, ShipmentAccessorial
from app.models.shipment import Shipment
from app.services.rating import rate_shipment


@pytest.fixture()
def staff(client, token_for):
    return {"Authorization": f"Bearer {token_for('admin')}"}


@pytest.fixture()
def rates(db_session):
    # Generic (null-lane) rate rows for a couple of classes + weight breaks.
    db_session.add_all([
        RateTable(weight_break_min=0, weight_break_max=1000, freight_class="100", rate_per_cwt=20.0, minimum_charge=110.0),
        RateTable(weight_break_min=1000, weight_break_max=5000, freight_class="100", rate_per_cwt=12.0, minimum_charge=110.0),
        RateTable(weight_break_min=0, weight_break_max=1000, freight_class="50", rate_per_cwt=10.0, minimum_charge=90.0),
    ])
    db_session.add(FuelSurcharge(effective_date=date(2025, 1, 1), percent=20.0))
    db_session.add(Accessorial(code="LIFTGATE", name="Liftgate", charge=45.0, per_hour=0))
    db_session.add(Accessorial(code="DETENTION", name="Detention", charge=65.0, per_hour=1))
    db_session.commit()


def _shipment(db_session, weight, fclass="100", pickup=date(2025, 6, 1)):
    s = Shipment(probill_number=f"PRATE{weight:.0f}{fclass}", total_weight_lbs=weight,
                 freight_class=fclass, pickup_date=pickup)
    db_session.add(s)
    db_session.commit()
    return s


# ── Rating ──
def test_rate_by_class_and_weight_break(db_session, rates):
    # 800 lbs, class 100 → break 0–1000 @ 20/cwt = 8cwt*20 = 160.
    s = _shipment(db_session, 800, "100")
    r = rate_shipment(db_session, s)
    freight = next(li for li in r["line_items"] if li["code"] == "FREIGHT")
    assert freight["amount"] == 160.0


def test_higher_weight_break_cheaper_rate(db_session, rates):
    # 2000 lbs, class 100 → break 1000–5000 @ 12/cwt = 20cwt*12 = 240.
    s = _shipment(db_session, 2000, "100")
    r = rate_shipment(db_session, s)
    freight = next(li for li in r["line_items"] if li["code"] == "FREIGHT")
    assert freight["amount"] == 240.0


def test_minimum_charge_applied(db_session, rates):
    # 100 lbs, class 100 → 1cwt*20 = 20, below min 110 → 110.
    s = _shipment(db_session, 100, "100")
    r = rate_shipment(db_session, s)
    freight = next(li for li in r["line_items"] if li["code"] == "FREIGHT")
    assert freight["amount"] == 110.0
    assert "minimum applied" in freight["description"]


def test_fuel_surcharge(db_session, rates):
    # 800 lbs class 100 = 160 freight; FSC 20% → 32.
    s = _shipment(db_session, 800, "100")
    r = rate_shipment(db_session, s)
    assert r["fuel_surcharge"] == 32.0
    assert r["total"] == 192.0  # 160 + 32


def test_accessorials(db_session, rates):
    s = _shipment(db_session, 800, "100")
    acc = db_session.query(Accessorial).filter_by(code="LIFTGATE").first()
    det = db_session.query(Accessorial).filter_by(code="DETENTION").first()
    db_session.add(ShipmentAccessorial(shipment_id=s.id, accessorial_id=acc.id, quantity=1))
    db_session.add(ShipmentAccessorial(shipment_id=s.id, accessorial_id=det.id, quantity=3))  # 3 hours
    db_session.commit()
    r = rate_shipment(db_session, s)
    # accessorials = 45 (liftgate) + 65*3 (detention) = 240
    assert r["accessorials_total"] == 240.0


def test_no_rate_returns_zero(db_session, rates):
    s = _shipment(db_session, 800, "500")  # no class 500 rate
    r = rate_shipment(db_session, s)
    assert r["total"] == 0.0


# ── Quotes endpoint ──
def test_quote_endpoint(client, staff, rates):
    resp = client.post("/quotes", headers=staff, json={"total_weight_lbs": 800, "freight_class": "100", "pickup_date": "2025-06-01"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 192.0


# ── Exceptions queue ──
def test_exceptions_queue_filters_and_status(client, staff, db_session):
    s = _shipment(db_session, 500, "100")
    created = client.post("/exceptions", headers=staff, json={
        "shipment_id": s.id, "type": "damage", "severity": "high", "description": "carton crushed"}).json()
    # Filter by type + severity.
    listed = client.get("/exceptions?type=damage&severity=high", headers=staff).json()
    assert any(e["id"] == created["id"] for e in listed["items"])
    # Resolve it.
    resolved = client.patch(f"/exceptions/{created['id']}", headers=staff,
                            json={"status": "resolved", "resolution_notes": "credit issued"}).json()
    assert resolved["status"] == "resolved"
    assert resolved["resolved_at"] is not None


# ── DQ-flag conversion on milestone ──
def test_data_quality_flag_becomes_exception(client, staff, db_session):
    # DELIVERED with no pickup → IMPOSSIBLE_SEQUENCE flag → data_quality exception.
    s = client.post("/shipments", headers=staff, json={}).json()
    client.post(f"/shipments/{s['id']}/milestones", headers=staff, json={"event_code": "DELIVERED", "source": "manual"})
    excs = client.get(f"/exceptions?shipment_id={s['id']}&type=data_quality", headers=staff).json()
    assert any(e["dq_code"] == "IMPOSSIBLE_SEQUENCE" for e in excs["items"])


# ── Freight bill draft on delivery ──
def test_freight_bill_draft_on_delivery_and_issue(client, staff, db_session, rates):
    s = client.post("/shipments", headers=staff, json={"total_weight_lbs": 800, "freight_class": "100"}).json()
    # Deliver (pickup first so it's not just an impossible seq — either way a bill drafts).
    client.post(f"/shipments/{s['id']}/milestones", headers=staff, json={"event_code": "PICKED_UP", "source": "manual"})
    client.post(f"/shipments/{s['id']}/milestones", headers=staff, json={"event_code": "DELIVERED", "source": "manual"})
    bills = client.get("/freight-bills?status=draft", headers=staff).json()
    mine = [b for b in bills["items"] if b["shipment_id"] == s["id"]]
    assert len(mine) == 1
    bill = mine[0]
    issued = client.post(f"/freight-bills/{bill['id']}/issue", headers=staff).json()
    assert issued["status"] == "issued"
    assert issued["issued_at"] is not None


# ── POD before delivery is a data-quality signal ──
def test_pod_without_delivery_flags(client, staff, db_session, tmp_path):
    s = client.post("/shipments", headers=staff, json={}).json()  # status BOOKED
    resp = client.post(
        f"/shipments/{s['id']}/documents", headers=staff,
        data={"type": "POD"},
        files={"file": ("pod.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert resp.status_code == 201
    # A POD_WITHOUT_DELIVERY exception was opened.
    excs = client.get(f"/exceptions?shipment_id={s['id']}&type=data_quality", headers=staff).json()
    assert any(e["dq_code"] == "POD_WITHOUT_DELIVERY" for e in excs["items"])
