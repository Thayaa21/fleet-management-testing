"""Auth endpoint tests: login, /auth/me, and role enforcement."""


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_login_success_returns_token_and_user(client, seeded_users):
    resp = client.post("/auth/login", json={"email": "admin@test.com", "password": "admin123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "admin@test.com"
    assert body["user"]["role"] == "admin"


def test_login_bad_password(client, seeded_users):
    resp = client.post("/auth/login", json={"email": "admin@test.com", "password": "nope"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email(client, seeded_users):
    resp = client.post("/auth/login", json={"email": "ghost@test.com", "password": "x"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_inactive_account(client, seeded_users):
    resp = client.post("/auth/login", json={"email": "inactive@test.com", "password": "inactive123"})
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ACCOUNT_INACTIVE"


def test_login_validation_error(client, seeded_users):
    resp = client.post("/auth/login", json={"email": "not-an-email", "password": "x"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


def test_me_requires_token(client, seeded_users):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHENTICATED"


def test_me_rejects_garbage_token(client, seeded_users):
    resp = client.get("/auth/me", headers=_auth("garbage.token.value"))
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_TOKEN"


def test_me_returns_current_user(client, token_for):
    resp = client.get("/auth/me", headers=_auth(token_for("customer")))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "customer@test.com"
    assert body["role"] == "customer_user"
    assert body["customer_id"] == 1


def test_staff_check_allows_staff_roles(client, token_for):
    for role in ("admin", "dispatcher", "dock"):
        resp = client.get("/auth/staff-check", headers=_auth(token_for(role)))
        assert resp.status_code == 200, role
        assert resp.json()["role"] == role


def test_staff_check_forbids_customer_user(client, token_for):
    resp = client.get("/auth/staff-check", headers=_auth(token_for("customer")))
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"]["code"] == "FORBIDDEN"
    assert body["error"]["details"]["your_role"] == "customer_user"


def test_request_id_header_present(client):
    resp = client.get("/health")
    assert resp.headers.get("X-Request-ID")


def test_request_id_echoed_when_supplied(client):
    resp = client.get("/health", headers={"X-Request-ID": "test-req-123"})
    assert resp.headers.get("X-Request-ID") == "test-req-123"
