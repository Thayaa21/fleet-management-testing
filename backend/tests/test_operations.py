"""Operations: end-to-end freight movement, fuzzy equipment resolution, and the
one-open-manifest-per-trailer guard."""
import pytest


@pytest.fixture()
def staff(client, token_for):
    return {"Authorization": f"Bearer {token_for('admin')}"}


def _terminal(client, staff, name):
    return client.post("/locations", headers=staff, json={"name": name, "type": "terminal"}).json()["id"]


def _trailer(client, staff, number):
    return client.post("/equipment/trailers", headers=staff, json={"trailer_number": number, "type": "dry_van"}).json()


def _shipment(client, staff):
    return client.post("/shipments", headers=staff, json={"bol_number": "OPS"}).json()


# ── Fuzzy equipment resolution ────────────────────────────
def test_unknown_trailer_returns_fuzzy_candidates(client, staff):
    _trailer(client, staff, "TRL1000")
    _trailer(client, staff, "TRL1001")
    # Near miss (distance 1 from TRL1000).
    resp = client.post("/manifests", headers=staff, json={"trailer_number": "TRL100O"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "UNKNOWN_EQUIPMENT_ID"
    assert "TRL1000" in body["error"]["details"]["candidates"]


def test_unknown_trailer_far_miss_empty_candidates(client, staff):
    _trailer(client, staff, "TRL1000")
    resp = client.post("/manifests", headers=staff, json={"trailer_number": "ZZZZZZZ"})
    assert resp.status_code == 422
    assert resp.json()["error"]["details"]["candidates"] == []


def test_trailer_number_normalized(client, staff):
    _trailer(client, staff, "trl2000")
    # lower-case input should resolve to the uppercased trailer.
    resp = client.post("/manifests", headers=staff, json={"trailer_number": " trl2000 "})
    assert resp.status_code == 201


# ── One open manifest per trailer ─────────────────────────
def test_trailer_cannot_be_on_two_open_manifests(client, staff):
    _trailer(client, staff, "TRL3000")
    first = client.post("/manifests", headers=staff, json={"trailer_number": "TRL3000"})
    assert first.status_code == 201
    second = client.post("/manifests", headers=staff, json={"trailer_number": "TRL3000"})
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "CONFLICT"


# ── Full end-to-end flow ──────────────────────────────────
def test_end_to_end_flow(client, staff):
    origin = _terminal(client, staff, "Origin Terminal E2E")
    dest = _terminal(client, staff, "Dest Terminal E2E")
    trailer = _trailer(client, staff, "E2E100")
    ship = _shipment(client, staff)
    sid = ship["id"]

    # Pickup request → dispatched → completed.
    pk = client.post("/pickups", headers=staff, json={"location_id": origin, "created_via": "manual"}).json()
    client.patch(f"/pickups/{pk['id']}", headers=staff, json={"status": "completed"})

    # Record the pickup on the shipment.
    r = client.post(f"/shipments/{sid}/milestones", headers=staff, json={"event_code": "PICKED_UP", "source": "driver_scan"})
    assert r.json()["current_status"] == "PICKED_UP"

    # Manifest at origin for the trailer, load the shipment.
    manifest = client.post("/manifests", headers=staff, json={
        "trailer_number": "E2E100", "origin_location_id": origin, "destination_location_id": dest,
    }).json()
    load = client.post(f"/manifests/{manifest['id']}/load", headers=staff, json={
        "trailer_number": "E2E100", "probill_number": ship["probill_number"], "handling_units_loaded": 2,
    })
    assert load.status_code == 201, load.text

    after_load = client.get(f"/shipments/{sid}", headers=staff).json()
    assert after_load["current_trailer_id"] == trailer["id"]
    assert after_load["current_status"] == "AT_ORIGIN_TERMINAL"  # LOADED_ON_TRAILER
    assert any(m["event_code"] == "LOADED_ON_TRAILER" for m in after_load["milestones"])

    # Linehaul trip, hook the trailer, dispatch.
    trip = client.post("/trips", headers=staff, json={
        "type": "linehaul", "origin_location_id": origin, "destination_location_id": dest,
    }).json()
    client.post(f"/trips/{trip['id']}/trailers", headers=staff, json={"trailer_number": "E2E100"})

    disp = client.post(f"/trips/{trip['id']}/dispatch", headers=staff)
    assert disp.status_code == 200
    after_disp = client.get(f"/shipments/{sid}", headers=staff).json()
    assert after_disp["current_status"] == "IN_LINEHAUL"
    assert after_disp["current_trip_id"] == trip["id"]
    assert any(m["event_code"] == "DEPARTED_TERMINAL" for m in after_disp["milestones"])

    # Arrive at destination.
    client.post(f"/trips/{trip['id']}/arrive", headers=staff)
    after_arrive = client.get(f"/shipments/{sid}", headers=staff).json()
    assert after_arrive["current_status"] == "AT_DESTINATION_TERMINAL"
    assert any(m["event_code"] == "ARRIVED_AT_DESTINATION_TERMINAL" for m in after_arrive["milestones"])

    # Unload clears the trailer.
    unload = client.post(f"/manifests/{manifest['id']}/unload", headers=staff, json={"probill_number": ship["probill_number"]})
    assert unload.status_code == 200
    after_unload = client.get(f"/shipments/{sid}", headers=staff).json()
    assert after_unload["current_trailer_id"] is None
    assert any(m["event_code"] == "UNLOADED" for m in after_unload["milestones"])

    # Out for delivery → delivered.
    client.post(f"/shipments/{sid}/milestones", headers=staff, json={"event_code": "OUT_FOR_DELIVERY", "source": "manual"})
    final = client.post(f"/shipments/{sid}/milestones", headers=staff, json={"event_code": "DELIVERED", "source": "driver_scan"})
    assert final.json()["current_status"] == "DELIVERED"

    # Audit rows exist across the lifecycle.
    audit = client.get(f"/audit?entity_type=shipments&entity_id={sid}&page_size=100", headers=staff).json()
    assert audit["total"] >= 5


def test_trailer_contents_and_tractor_current_trip(client, staff):
    origin = _terminal(client, staff, "Contents Terminal")
    trailer = _trailer(client, staff, "CON100")
    ship = _shipment(client, staff)
    manifest = client.post("/manifests", headers=staff, json={"trailer_number": "CON100", "origin_location_id": origin}).json()
    client.post(f"/manifests/{manifest['id']}/load", headers=staff, json={"probill_number": ship["probill_number"]})

    contents = client.get(f"/equipment/trailers/{trailer['id']}/contents", headers=staff).json()
    assert any(c["probill_number"] == ship["probill_number"] for c in contents["contents"])

    # Tractor with a planned trip.
    tractor = client.post("/equipment/tractors", headers=staff, json={"unit_number": "CONTRACT1"}).json()
    trip = client.post("/trips", headers=staff, json={"type": "linehaul", "tractor_id": tractor["id"]}).json()
    ct = client.get(f"/equipment/tractors/{tractor['id']}/current-trip", headers=staff).json()
    assert ct["trip"]["id"] == trip["id"]


def test_load_trailer_mismatch_409(client, staff):
    _trailer(client, staff, "MAN100")
    _trailer(client, staff, "MAN200")
    ship = _shipment(client, staff)
    manifest = client.post("/manifests", headers=staff, json={"trailer_number": "MAN100"}).json()
    # Load with a valid but different trailer number.
    resp = client.post(f"/manifests/{manifest['id']}/load", headers=staff, json={
        "trailer_number": "MAN200", "probill_number": ship["probill_number"],
    })
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "TRAILER_MISMATCH"
