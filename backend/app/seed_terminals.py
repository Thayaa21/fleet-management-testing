"""Seed the carrier's terminals and US cross-border points.

Run from the backend/ directory (after `alembic upgrade head`):
    python -m app.seed_terminals
"""
from sqlalchemy import select

from app.db import SessionLocal
from app.models.location import Location, LocationType

# name, type, city, province_state, country, lat, lng, timezone
TERMINALS = [
    ("Mississauga Hub", LocationType.terminal, "Mississauga", "ON", "CA", 43.5890, -79.6441, "America/Toronto"),
    ("Montreal Terminal", LocationType.terminal, "Montreal", "QC", "CA", 45.5019, -73.5674, "America/Toronto"),
    ("Ottawa Terminal", LocationType.terminal, "Ottawa", "ON", "CA", 45.4215, -75.6972, "America/Toronto"),
    ("Winnipeg Terminal", LocationType.terminal, "Winnipeg", "MB", "CA", 49.8951, -97.1384, "America/Winnipeg"),
    ("Calgary Terminal", LocationType.terminal, "Calgary", "AB", "CA", 51.0447, -114.0719, "America/Edmonton"),
    ("Edmonton Terminal", LocationType.terminal, "Edmonton", "AB", "CA", 53.5461, -113.4938, "America/Edmonton"),
    ("Vancouver Terminal", LocationType.terminal, "Vancouver", "BC", "CA", 49.2827, -123.1207, "America/Vancouver"),
    # US cross-border points
    ("Buffalo Crossing", LocationType.customs_point, "Buffalo", "NY", "US", 42.8864, -78.8784, "America/New_York"),
    ("Detroit Crossing", LocationType.customs_point, "Detroit", "MI", "US", 42.3314, -83.0458, "America/Detroit"),
    ("Blaine Crossing", LocationType.customs_point, "Blaine", "WA", "US", 48.9937, -122.7466, "America/Los_Angeles"),
]


def seed() -> None:
    db = SessionLocal()
    created, skipped = 0, 0
    try:
        for name, type_, city, prov, country, lat, lng, tz in TERMINALS:
            existing = db.scalar(select(Location).where(Location.name == name))
            if existing:
                skipped += 1
                continue
            db.add(
                Location(
                    name=name, type=type_, city=city, province_state=prov, country=country,
                    lat=lat, lng=lng, timezone=tz,
                )
            )
            created += 1
        db.commit()
        print(f"Terminal seed complete: {created} created, {skipped} already existed.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
