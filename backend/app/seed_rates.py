"""Seed a small generic rate table, fuel surcharge, and accessorials catalog.

Run from the backend/ directory (after `alembic upgrade head`):
    python -m app.seed_rates

The rate table uses NULL lanes (generic fallback), so any lane rates by weight
break + freight class until lane-specific rows are added.
"""
from datetime import date

from sqlalchemy import select

from app.db import SessionLocal
from app.models.billing import Accessorial, FuelSurcharge, RateTable

# (weight_min, weight_max, class, rate_per_cwt, minimum_charge)
RATE_ROWS = [
    (0, 500, "50", 12.0, 95.0),
    (0, 500, "70", 15.0, 95.0),
    (0, 500, "100", 20.0, 110.0),
    (0, 500, "125", 24.0, 120.0),
    (0, 500, "150", 28.0, 130.0),
    (500, 1000, "50", 10.0, 95.0),
    (500, 1000, "100", 17.0, 110.0),
    (500, 1000, "125", 20.0, 120.0),
    (500, 1000, "150", 24.0, 130.0),
    (1000, 2000, "50", 8.5, 95.0),
    (1000, 2000, "100", 14.0, 110.0),
    (1000, 2000, "125", 17.0, 120.0),
    (1000, 2000, "150", 20.0, 130.0),
    (2000, 5000, "50", 7.0, 95.0),
    (2000, 5000, "100", 11.5, 110.0),
    (2000, 5000, "125", 14.0, 120.0),
    (2000, 5000, "150", 16.5, 130.0),
    (5000, 10000, "100", 9.0, 110.0),
    (5000, 10000, "125", 11.0, 120.0),
    (10000, None, "100", 7.5, 110.0),
    (10000, None, "125", 9.0, 120.0),
]

ACCESSORIALS = [
    ("LIFTGATE", "Liftgate", 45.0, 0),
    ("RESIDENTIAL", "Residential delivery", 55.0, 0),
    ("INSIDE", "Inside delivery", 60.0, 0),
    ("APPOINTMENT", "Appointment", 25.0, 0),
    ("HAZMAT", "Hazardous materials", 75.0, 0),
    ("LIMITED_ACCESS", "Limited access", 50.0, 0),
    ("DETENTION", "Detention (per hour)", 65.0, 1),
]


def seed() -> None:
    db = SessionLocal()
    created = {"rates": 0, "fsc": 0, "acc": 0}
    try:
        if db.scalar(select(RateTable).limit(1)) is None:
            for wmin, wmax, cls, rate, minc in RATE_ROWS:
                db.add(RateTable(origin_terminal_id=None, destination_terminal_id=None,
                                 weight_break_min=wmin, weight_break_max=wmax,
                                 freight_class=cls, rate_per_cwt=rate, minimum_charge=minc))
                created["rates"] += 1

        if db.scalar(select(FuelSurcharge).limit(1)) is None:
            db.add(FuelSurcharge(effective_date=date(2025, 1, 1), percent=18.0))
            db.add(FuelSurcharge(effective_date=date(2026, 1, 1), percent=20.0))
            created["fsc"] += 2

        for code, name, charge, per_hour in ACCESSORIALS:
            if db.scalar(select(Accessorial).where(Accessorial.code == code)) is None:
                db.add(Accessorial(code=code, name=name, charge=charge, per_hour=per_hour))
                created["acc"] += 1

        db.commit()
        print(f"Rate seed complete: {created['rates']} rate rows, {created['fsc']} FSC rows, {created['acc']} accessorials.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
