"""Pytest fixtures: isolated in-memory DB, TestClient, and per-role users."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.services.audit import register_audit_listeners, reset_audit_context
from app.services.security import hash_password


@pytest.fixture()
def db_session():
    # A single shared in-memory SQLite connection for the test.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    register_audit_listeners(TestingSession)
    reset_audit_context()
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def seeded_users(db_session):
    users = {
        "admin": User(email="admin@test.com", password_hash=hash_password("admin123"),
                      full_name="Admin", role=UserRole.admin, is_active=True),
        "dispatcher": User(email="dispatcher@test.com", password_hash=hash_password("dispatch123"),
                           full_name="Dispatcher", role=UserRole.dispatcher, is_active=True),
        "dock": User(email="dock@test.com", password_hash=hash_password("dock123"),
                     full_name="Dock", role=UserRole.dock, is_active=True),
        "customer": User(email="customer@test.com", password_hash=hash_password("customer123"),
                         full_name="Customer", role=UserRole.customer_user, customer_id=1, is_active=True),
        "inactive": User(email="inactive@test.com", password_hash=hash_password("inactive123"),
                         full_name="Inactive", role=UserRole.dispatcher, is_active=False),
    }
    db_session.add_all(users.values())
    db_session.commit()
    return users


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _login(client, email, password):
    return client.post("/auth/login", json={"email": email, "password": password})


@pytest.fixture()
def token_for(client, seeded_users):
    """Return a helper that logs in a seeded role and returns its bearer token."""
    creds = {
        "admin": ("admin@test.com", "admin123"),
        "dispatcher": ("dispatcher@test.com", "dispatch123"),
        "dock": ("dock@test.com", "dock123"),
        "customer": ("customer@test.com", "customer123"),
    }

    def _get(role: str) -> str:
        email, password = creds[role]
        resp = _login(client, email, password)
        assert resp.status_code == 200, resp.text
        return resp.json()["access_token"]

    return _get
