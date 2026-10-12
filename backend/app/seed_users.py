"""Seed one user per role for local development.

Run from the backend/ directory (after `alembic upgrade head`):
    python -m app.seed_users

Credentials are documented in backend/README.md and are for DEV ONLY.
"""
from sqlalchemy import select

from app.db import SessionLocal
from app.models.user import User, UserRole
from app.services.security import hash_password

# (email, password, full_name, role, customer_id)
SEED_USERS = [
    ("admin@example.com", "admin123", "Ada Admin", UserRole.admin, None),
    ("dispatcher@example.com", "dispatch123", "Dev Dispatcher", UserRole.dispatcher, None),
    ("dock@example.com", "dock123", "Dana Dock", UserRole.dock, None),
    ("customer@example.com", "customer123", "Casey Customer", UserRole.customer_user, 1),
]


def seed() -> None:
    db = SessionLocal()
    created, skipped = 0, 0
    try:
        for email, password, full_name, role, customer_id in SEED_USERS:
            existing = db.scalar(select(User).where(User.email == email))
            if existing:
                skipped += 1
                continue
            db.add(
                User(
                    email=email,
                    password_hash=hash_password(password),
                    full_name=full_name,
                    role=role,
                    customer_id=customer_id,
                    is_active=True,
                )
            )
            created += 1
        db.commit()
        print(f"Seed complete: {created} created, {skipped} already existed.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
