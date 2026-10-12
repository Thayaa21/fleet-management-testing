"""Customer API gateway: each error_code path, tracking (city-level), idempotency,
and no-secret-leak."""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.api import ApiClient, ApiKey, IpAllowlist
from app.services.api_keys import create_api_key


@pytest.fixture()
def staff(client, token_for):
    return {"Authorization": f"Bearer {token_for('admin')}"}


@pytest.fixture()
def customer_and_client(db_session):
    from app.models.customer import Customer, CustomerType
    cust = Customer(account_number="APICUST", name="API Customer", type=CustomerType.both)
    db_session.add(cust)
    db_session.flush()
    api_client = ApiClient(customer_id=cust.id, name="Acme")
    db_session.add(api_client)
    db_session.flush()
    db_session.commit()
    return cust, api_client


def _make_key(db_session, api_client, scopes, expires_at=None):
    row, full = create_api_key(db_session, api_client.id, scopes, expires_at)
    db_session.commit()
    return row, full


# ── Error-code paths ──
def test_missing_api_key(client, customer_and_client):
    resp = client.get("/api/v1/tracking/P0000001")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "MISSING_API_KEY"


def test_invalid_api_key(client, customer_and_client):
    resp = client.get("/api/v1/tracking/P0000001", headers={"X-API-Key": "tms_deadbeef_nope"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_API_KEY"


def test_expired_api_key(client, db_session, customer_and_client):
    _, api_client = customer_and_client
    _, full = _make_key(db_session, api_client, ["tracking:read"], expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    resp = client.get("/api/v1/tracking/P0000001", headers={"X-API-Key": full})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "EXPIRED_API_KEY"


def test_revoked_api_key(client, db_session, customer_and_client):
    _, api_client = customer_and_client
    row, full = _make_key(db_session, api_client, ["tracking:read"])
    row.revoked_at = datetime.now(timezone.utc)
    db_session.commit()
    resp = client.get("/api/v1/tracking/P0000001", headers={"X-API-Key": full})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "REVOKED_API_KEY"


def test_insufficient_scope(client, db_session, customer_and_client):
    _, api_client = customer_and_client
    _, full = _make_key(db_session, api_client, ["pickups:write"])  # missing tracking:read
    resp = client.get("/api/v1/tracking/P0000001", headers={"X-API-Key": full})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "INSUFFICIENT_SCOPE"


def test_ip_not_allowed(client, db_session, customer_and_client):
    _, api_client = customer_and_client
    _, full = _make_key(db_session, api_client, ["tracking:read"])
    db_session.add(IpAllowlist(api_client_id=api_client.id, cidr="10.0.0.0/8", label="corp"))
    db_session.commit()
    # TestClient source ip is testclient/127.0.0.1, not in 10.0.0.0/8.
    resp = client.get("/api/v1/tracking/P0000001", headers={"X-API-Key": full})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "IP_NOT_ALLOWED"


def test_unknown_probill(client, db_session, customer_and_client):
    _, api_client = customer_and_client
    _, full = _make_key(db_session, api_client, ["tracking:read"])
    resp = client.get("/api/v1/tracking/PNOPE", headers={"X-API-Key": full})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "UNKNOWN_PROBILL"


# ── Tracking success + city-level only ──
def test_tracking_returns_city_level_only(client, db_session, staff, customer_and_client):
    cust, api_client = customer_and_client
    _, full = _make_key(db_session, api_client, ["tracking:read"])
    # A shipment for this customer, currently at a location.
    from app.models.location import Location, LocationType
    from app.models.shipment import Shipment
    loc = Location(name="Loc", type=LocationType.terminal, city="Mississauga", province_state="ON", country="CA",
                   lat=43.5, lng=-79.6)
    db_session.add(loc)
    db_session.flush()
    ship = Shipment(probill_number="PTRACK1", customer_id=cust.id, current_location_id=loc.id)
    db_session.add(ship)
    db_session.commit()

    resp = client.get("/api/v1/tracking/PTRACK1", headers={"X-API-Key": full})
    assert resp.status_code == 200
    body = resp.json()
    assert body["last_known_position"] == "Mississauga, ON, CA"
    # No raw coordinates leak to the customer.
    assert "lat" not in str(body)
    assert "lng" not in str(body)


# ── Book shipment + idempotency ──
def test_book_shipment_and_idempotency(client, db_session, customer_and_client):
    _, api_client = customer_and_client
    _, full = _make_key(db_session, api_client, ["shipments:write"])
    payload = {
        "shipper_city": "Toronto", "shipper_province_state": "ON", "shipper_postal_zip": "M5V",
        "shipper_country": "CA", "consignee_city": "Buffalo", "consignee_province_state": "NY",
        "consignee_postal_zip": "14201", "consignee_country": "US",
        "pickup_date": "2026-10-01", "total_weight_lbs": 1200,
    }
    h = {"X-API-Key": full, "Idempotency-Key": "abc-123"}
    first = client.post("/api/v1/shipments", headers=h, json=payload)
    assert first.status_code == 201, first.text
    probill = first.json()["probill_number"]
    # Same idempotency key returns the original response.
    second = client.post("/api/v1/shipments", headers=h, json=payload)
    assert second.json()["probill_number"] == probill


def test_validation_error_shape(client, db_session, customer_and_client):
    _, api_client = customer_and_client
    _, full = _make_key(db_session, api_client, ["shipments:write"])
    resp = client.post("/api/v1/shipments", headers={"X-API-Key": full}, json={"total_weight_lbs": "heavy"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


# ── Logging + no secret leak ──
def test_every_request_logged_and_key_redacted(client, staff, db_session, customer_and_client):
    _, api_client = customer_and_client
    _, full = _make_key(db_session, api_client, ["tracking:read"])
    client.get("/api/v1/tracking/PNOPE", headers={"X-API-Key": full})  # UNKNOWN_PROBILL, logged
    logs = client.get("/integrations/api-logs", headers=staff).json()
    assert logs["total"] >= 1
    # No stored log echoes the full key.
    for row in logs["items"]:
        assert "tms_" not in (row.get("key_prefix") or "")  # only prefix stored, not full key


def test_rate_limited(client, db_session, customer_and_client, monkeypatch):
    import app.services.api_gateway as gw
    # Tighten the limit and reset buckets so this test is deterministic.
    monkeypatch.setattr(gw, "RATE_LIMIT_MAX", 3)
    gw._BUCKETS.clear()
    _, api_client = customer_and_client
    _, full = _make_key(db_session, api_client, ["tracking:read"])
    h = {"X-API-Key": full}
    codes = [client.get("/api/v1/tracking/PNOPE", headers=h).status_code for _ in range(5)]
    assert 429 in codes
    gw._BUCKETS.clear()


def test_key_hash_never_equals_prefix(db_session, customer_and_client):
    _, api_client = customer_and_client
    row, full = _make_key(db_session, api_client, ["tracking:read"])
    assert row.key_hash != row.key_prefix
    assert row.key_hash not in full  # hash of full key isn't a substring of it
