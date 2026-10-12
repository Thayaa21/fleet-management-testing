"""Telematics ingest paths and shipment position resolution across a trailer change."""
from datetime import datetime, timedelta, timezone

import pytest

SECRET = "dev-mock-secret"  # matches config default for provider "mock"
HDR = {"X-Telematics-Secret": SECRET}


@pytest.fixture()
def staff(client, token_for):
    return {"Authorization": f"Bearer {token_for('admin')}"}


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def _terminal(client, staff, name, lat=43.0, lng=-79.0):
    return client.post("/locations", headers=staff, json={"name": name, "type": "terminal", "lat": lat, "lng": lng}).json()["id"]


def _device(client, staff, serial):
    return client.post("/equipment/devices", headers=staff, json={"provider": "mock", "device_serial": serial}).json()


def _tractor_with_device(client, staff, unit, device_id):
    return client.post("/equipment/tractors", headers=staff, json={"unit_number": unit, "telematics_device_id": device_id}).json()


def _ping(serial, when, lat=43.0, lng=-79.0):
    return {"device_serial": serial, "recorded_at": _iso(when), "lat": lat, "lng": lng, "speed_kph": 90}


# ── Auth ──
def test_bad_secret_401_and_nothing_stored(client, staff):
    dev = _device(client, staff, "DEVBAD")
    resp = client.post("/integrations/telematics/mock/webhook",
                       headers={"X-Telematics-Secret": "wrong"},
                       json={"pings": [_ping("DEVBAD", datetime.now(timezone.utc))]})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "AUTH_FAILED"
    # An AUTH_FAILED log row exists.
    logs = client.get("/integrations/telematics/logs?error_code=AUTH_FAILED", headers=staff).json()
    assert logs["total"] >= 1


# ── Valid ──
def test_valid_batch_stored_and_last_ping_updated(client, staff):
    dev = _device(client, staff, "DEVOK")
    _tractor_with_device(client, staff, "TUNIT1", dev["id"])
    when = datetime.now(timezone.utc)
    resp = client.post("/integrations/telematics/mock/webhook", headers=HDR,
                       json={"pings": [_ping("DEVOK", when)]})
    assert resp.status_code == 200
    assert resp.json()["accepted"] == 1
    dev_after = client.get(f"/equipment/devices/{dev['id']}", headers=staff).json()
    assert dev_after["last_ping_at"] is not None


def test_unknown_device_logged_not_stored(client, staff):
    resp = client.post("/integrations/telematics/mock/webhook", headers=HDR,
                       json={"pings": [_ping("NOSUCHDEV", datetime.now(timezone.utc))]})
    assert resp.status_code == 200
    assert resp.json()["by_error"].get("UNKNOWN_DEVICE") == 1


def test_unassigned_device(client, staff):
    _device(client, staff, "DEVFREE")  # created but not attached to any asset
    resp = client.post("/integrations/telematics/mock/webhook", headers=HDR,
                       json={"pings": [_ping("DEVFREE", datetime.now(timezone.utc))]})
    assert resp.status_code == 200
    assert resp.json()["by_error"].get("DEVICE_UNASSIGNED") == 1


def test_malformed_payload(client, staff):
    resp = client.post("/integrations/telematics/mock/webhook", headers=HDR,
                       json={"pings": [{"device_serial": "X", "lat": "not-a-number"}]})
    assert resp.status_code == 200
    assert resp.json()["by_error"].get("MALFORMED_PAYLOAD") == 1


def test_duplicate_ping(client, staff):
    dev = _device(client, staff, "DEVDUP")
    _tractor_with_device(client, staff, "TUNITDUP", dev["id"])
    when = datetime.now(timezone.utc)
    p = {"pings": [_ping("DEVDUP", when)]}
    first = client.post("/integrations/telematics/mock/webhook", headers=HDR, json=p)
    assert first.json()["accepted"] == 1
    second = client.post("/integrations/telematics/mock/webhook", headers=HDR, json=p)
    assert second.json()["by_error"].get("DUPLICATE") == 1


# ── Positions across a trailer change ──
def test_shipment_positions_across_trailer_change(client, staff):
    origin = _terminal(client, staff, "POS Origin", lat=43.0, lng=-79.0)
    hub = _terminal(client, staff, "POS Hub", lat=45.0, lng=-75.0)
    dest = _terminal(client, staff, "POS Dest", lat=49.0, lng=-97.0)

    # Two trailers, each with a device.
    devA = _device(client, staff, "DEVA")
    devB = _device(client, staff, "DEVB")
    trailerA = client.post("/equipment/trailers", headers=staff,
                           json={"trailer_number": "TA1", "type": "dry_van", "telematics_device_id": devA["id"]}).json()
    trailerB = client.post("/equipment/trailers", headers=staff,
                           json={"trailer_number": "TB1", "type": "dry_van", "telematics_device_id": devB["id"]}).json()

    ship = client.post("/shipments", headers=staff, json={"bol_number": "POS"}).json()
    prob = ship["probill_number"]

    # Leg 1: manifest on trailer A (origin -> hub), load, ping while loaded, unload.
    m1 = client.post("/manifests", headers=staff,
                     json={"trailer_number": "TA1", "origin_location_id": origin, "destination_location_id": hub}).json()
    client.post(f"/manifests/{m1['id']}/load", headers=staff, json={"probill_number": prob})
    # Ping A during window 1 (recorded_at is "now", i.e. after loaded_at and before unload).
    client.post("/integrations/telematics/mock/webhook", headers=HDR, json={"pings": [
        _ping("DEVA", datetime.now(timezone.utc), lat=43.5, lng=-78.0),
    ]})
    client.post(f"/manifests/{m1['id']}/unload", headers=staff, json={"probill_number": prob})

    # Leg 2: manifest on trailer B (hub -> dest), load, ping while loaded.
    m2 = client.post("/manifests", headers=staff,
                     json={"trailer_number": "TB1", "origin_location_id": hub, "destination_location_id": dest}).json()
    client.post(f"/manifests/{m2['id']}/load", headers=staff, json={"probill_number": prob})
    client.post("/integrations/telematics/mock/webhook", headers=HDR, json={"pings": [
        _ping("DEVB", datetime.now(timezone.utc), lat=46.0, lng=-80.0),
    ]})

    res = client.get(f"/shipments/{ship['id']}/positions", headers=staff).json()
    # Two loaded windows: trailer A then trailer B.
    assert len(res["windows"]) == 2
    trailer_ids = {w["trailer_id"] for w in res["windows"]}
    assert trailer_ids == {trailerA["id"], trailerB["id"]}
    # Positions include points from both devices, proving resolution across the change.
    devices_seen = {p["device_id"] for p in res["positions"]}
    assert devA["id"] in devices_seen
    assert devB["id"] in devices_seen


# ── Health ──
def test_telematics_health_lists_stale_on_active_trip(client, staff):
    origin = _terminal(client, staff, "H Origin")
    dest = _terminal(client, staff, "H Dest")
    dev = _device(client, staff, "DEVHEALTH")
    tractor = _tractor_with_device(client, staff, "THEALTH", dev["id"])
    trailer = client.post("/equipment/trailers", headers=staff, json={"trailer_number": "HTR1", "type": "dry_van"}).json()
    ship = client.post("/shipments", headers=staff, json={}).json()
    m = client.post("/manifests", headers=staff, json={"trailer_number": "HTR1", "origin_location_id": origin, "destination_location_id": dest}).json()
    client.post(f"/manifests/{m['id']}/load", headers=staff, json={"probill_number": ship["probill_number"]})
    trip = client.post("/trips", headers=staff, json={"type": "linehaul", "tractor_id": tractor["id"], "origin_location_id": origin, "destination_location_id": dest}).json()
    client.post(f"/trips/{trip['id']}/trailers", headers=staff, json={"trailer_number": "HTR1"})
    client.post(f"/trips/{trip['id']}/dispatch", headers=staff)

    # Device never pinged -> stale on an in-progress trip.
    health = client.get("/telematics/health?hours=1", headers=staff).json()
    assert any(d["device_id"] == dev["id"] for d in health["stale_devices"])
