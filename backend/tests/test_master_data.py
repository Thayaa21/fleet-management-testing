"""Master-data CRUD, pagination, search, filters, uniqueness, soft delete,
and device attach/detach tests."""
import pytest


@pytest.fixture()
def staff(client, token_for):
    return {"Authorization": f"Bearer {token_for('admin')}"}


@pytest.fixture()
def customer_headers(client, token_for):
    return {"Authorization": f"Bearer {token_for('customer')}"}


# ── Access control ────────────────────────────────────────
def test_master_data_requires_staff(client, customer_headers):
    resp = client.get("/customers", headers=customer_headers)
    assert resp.status_code == 403


def test_master_data_requires_auth(client, seeded_users):
    assert client.get("/customers").status_code == 401


# ── Customers CRUD ────────────────────────────────────────
def _make_customer(client, staff, account="ACME01", name="Acme Corp"):
    return client.post("/customers", headers=staff, json={
        "account_number": account, "name": name, "type": "shipper",
    })


def test_create_and_get_customer(client, staff):
    resp = _make_customer(client, staff)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["account_number"] == "ACME01"
    assert body["status"] == "active"

    got = client.get(f"/customers/{body['id']}", headers=staff)
    assert got.status_code == 200
    assert got.json()["name"] == "Acme Corp"


def test_account_number_normalized_uppercase(client, staff):
    resp = client.post("/customers", headers=staff, json={
        "account_number": "  lower01 ", "name": "X", "type": "both",
    })
    assert resp.status_code == 201
    assert resp.json()["account_number"] == "LOWER01"


def test_duplicate_account_number_409(client, staff):
    _make_customer(client, staff, account="DUP1")
    resp = _make_customer(client, staff, account="DUP1", name="Other")
    assert resp.status_code == 409
    body = resp.json()
    assert body["error"]["code"] == "CONFLICT"
    assert body["error"]["details"]["field"] == "account_number"


def test_update_customer(client, staff):
    cid = _make_customer(client, staff).json()["id"]
    resp = client.patch(f"/customers/{cid}", headers=staff, json={"credit_hold": True, "name": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["credit_hold"] is True
    assert resp.json()["name"] == "Renamed"


def test_soft_delete_customer(client, staff):
    cid = _make_customer(client, staff).json()["id"]
    resp = client.delete(f"/customers/{cid}", headers=staff)
    assert resp.status_code == 200
    assert resp.json()["status"] == "inactive"
    # Row still fetchable by id.
    assert client.get(f"/customers/{cid}", headers=staff).status_code == 200
    # Excluded from default list.
    listed = client.get("/customers", headers=staff).json()
    assert all(c["id"] != cid for c in listed["items"])
    # Included when opted in.
    listed_inc = client.get("/customers?include_inactive=true", headers=staff).json()
    assert any(c["id"] == cid for c in listed_inc["items"])


def test_customer_pagination_and_search(client, staff):
    for i in range(25):
        _make_customer(client, staff, account=f"PAG{i:03d}", name=f"Paginated {i}")
    page1 = client.get("/customers?page=1&page_size=10", headers=staff).json()
    assert page1["total"] >= 25
    assert page1["page"] == 1 and page1["page_size"] == 10
    assert len(page1["items"]) == 10

    found = client.get("/customers?q=Paginated 7", headers=staff).json()
    assert any("Paginated 7" == c["name"] for c in found["items"])


def test_customer_filter_by_type(client, staff):
    _make_customer(client, staff, account="SHIP1", name="Shipper One")
    client.post("/customers", headers=staff, json={"account_number": "PAY1", "name": "Payer", "type": "third_party_payer"})
    resp = client.get("/customers?type=third_party_payer", headers=staff).json()
    assert all(c["type"] == "third_party_payer" for c in resp["items"])
    assert any(c["account_number"] == "PAY1" for c in resp["items"])


# ── Locations + FK validation ─────────────────────────────
def test_location_bad_customer_fk_422(client, staff):
    resp = client.post("/locations", headers=staff, json={
        "name": "Ghost Site", "type": "customer_site", "customer_id": 99999,
    })
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_REFERENCE"


def test_create_terminal_location(client, staff):
    resp = client.post("/locations", headers=staff, json={
        "name": "Test Terminal", "type": "terminal", "country": "CA",
    })
    assert resp.status_code == 201
    assert resp.json()["geofence_radius_m"] == 300


# ── Drivers ───────────────────────────────────────────────
def test_driver_crud_and_unique(client, staff):
    r = client.post("/drivers", headers=staff, json={
        "employee_number": "emp1", "full_name": "Pat Driver", "type": "linehaul",
    })
    assert r.status_code == 201
    assert r.json()["employee_number"] == "EMP1"
    dup = client.post("/drivers", headers=staff, json={
        "employee_number": "EMP1", "full_name": "Other", "type": "city_pd",
    })
    assert dup.status_code == 409


# ── Equipment + device attach rule ────────────────────────
def _terminal(client, staff):
    return client.post("/locations", headers=staff, json={"name": "T", "type": "terminal"}).json()["id"]


def _device(client, staff, serial):
    return client.post("/equipment/devices", headers=staff, json={"provider": "mock", "device_serial": serial}).json()


def test_tractor_with_device_attaches(client, staff):
    term = _terminal(client, staff)
    dev = _device(client, staff, "DEV001")
    resp = client.post("/equipment/tractors", headers=staff, json={
        "unit_number": "t100", "home_terminal_id": term, "telematics_device_id": dev["id"],
    })
    assert resp.status_code == 201
    assert resp.json()["unit_number"] == "T100"
    # Device now reports attached to the tractor.
    got = client.get(f"/equipment/devices/{dev['id']}", headers=staff).json()
    assert got["attached_to_type"] == "tractor"
    assert got["attached_to_id"] == resp.json()["id"]
    assert got["status"] == "active"


def test_device_single_attach_detaches_prior(client, staff):
    term = _terminal(client, staff)
    dev = _device(client, staff, "DEV777")
    t1 = client.post("/equipment/tractors", headers=staff, json={
        "unit_number": "T1", "home_terminal_id": term, "telematics_device_id": dev["id"],
    }).json()
    t2 = client.post("/equipment/tractors", headers=staff, json={
        "unit_number": "T2", "home_terminal_id": term,
    }).json()
    # Move the device to t2.
    client.patch(f"/equipment/tractors/{t2['id']}", headers=staff, json={"telematics_device_id": dev["id"]})

    t1_after = client.get(f"/equipment/tractors/{t1['id']}", headers=staff).json()
    t2_after = client.get(f"/equipment/tractors/{t2['id']}", headers=staff).json()
    dev_after = client.get(f"/equipment/devices/{dev['id']}", headers=staff).json()
    assert t1_after["telematics_device_id"] is None       # prior detached
    assert t2_after["telematics_device_id"] == dev["id"]  # now on t2
    assert dev_after["attached_to_id"] == t2["id"]


def test_detach_device_sets_unassigned(client, staff):
    term = _terminal(client, staff)
    dev = _device(client, staff, "DEV900")
    t = client.post("/equipment/tractors", headers=staff, json={
        "unit_number": "TT9", "home_terminal_id": term, "telematics_device_id": dev["id"],
    }).json()
    client.patch(f"/equipment/tractors/{t['id']}", headers=staff, json={"telematics_device_id": None})
    dev_after = client.get(f"/equipment/devices/{dev['id']}", headers=staff).json()
    assert dev_after["attached_to_type"] == "none"
    assert dev_after["attached_to_id"] is None
    assert dev_after["status"] == "unassigned"


def test_trailer_crud(client, staff):
    term = _terminal(client, staff)
    resp = client.post("/equipment/trailers", headers=staff, json={
        "trailer_number": "trl1", "type": "dry_van", "home_terminal_id": term,
        "capacity_lbs": 40000, "capacity_cuft": 3800,
    })
    assert resp.status_code == 201
    assert resp.json()["trailer_number"] == "TRL1"
    dup = client.post("/equipment/trailers", headers=staff, json={"trailer_number": "TRL1", "type": "pup"})
    assert dup.status_code == 409
