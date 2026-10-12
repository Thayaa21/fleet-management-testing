"""Import orders.csv (repo root) into customers, locations, and shipments.

Run from the backend/ directory (after `alembic upgrade head`):
    python -m app.import_orders [path/to/orders.csv]

Mapping assumptions (kept intentionally simple and honest; dirty data is
preserved and FLAGGED via shipments.data_quality_flags rather than cleaned):

- Bill-to customer: the CSV has no customer identity, so a single synthetic
  account "IMPORTED" is created and used as bill-to for every imported shipment.
- Locations: origin_zip / dest_zip become customer_site locations, created on
  demand keyed by (postal, country). Country is normalized
  (US/USA/United States -> US; CA/Canada -> CA); the ORIGINAL value is kept in a
  DQ note when it was non-canonical.
- probill_number: generated as P####### (continues the existing sequence). The
  original CSV shipment_id is stored in customer_reference.
- Flags: weight_lbs, freight_class, is_stackable, is_urgent, delivery_appointment
  map directly. is_cross_border = origin_country != dest_country.
- skid_dims: parsed into one handling unit when it looks like LxWxH (optionally
  with a unit suffix); "unknown"/blank -> DQ flag DIMS_UNKNOWN.
- Quote: dirty free-text; NOT used for rating. Unparseable/blank -> DQ flag
  QUOTE_UNPARSEABLE. Parsed numeric value (if any) kept in a note.
- dest/origin postal that doesn't look like a US ZIP or CA postal -> DQ flag
  BAD_POSTAL, still imported.
- created_by = "import", source = import.
"""
import csv
import os
import re
import sys
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.models.customer import Customer, CustomerStatus, CustomerType
from app.models.location import Location, LocationType
from app.models.shipment import (
    HandlingUnit,
    HandlingUnitType,
    Shipment,
    ShipmentSource,
)

DEFAULT_CSV = os.path.join(os.path.dirname(__file__), "..", "..", "orders.csv")

US_ZIP = re.compile(r"^\d{5}$")
CA_POSTAL = re.compile(r"^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$")
DIMS = re.compile(r"^\s*(\d+)\s*[xX]\s*(\d+)\s*[xX]\s*(\d+)")


def _norm_country(raw: str) -> tuple[str, bool]:
    """Return (canonical 2-letter, was_non_canonical)."""
    v = (raw or "").strip().lower()
    if v in ("us", "usa", "united states"):
        return "US", raw.strip() != "US"
    if v in ("ca", "canada"):
        return "CA", raw.strip() != "CA"
    return (raw or "").strip().upper()[:2], True


def _to_bool(v: str) -> bool:
    return str(v).strip().lower() in ("true", "1", "yes")


def _get_or_create_customer(db) -> Customer:
    cust = db.scalar(select(Customer).where(Customer.account_number == "IMPORTED"))
    if cust is None:
        cust = Customer(account_number="IMPORTED", name="Imported (orders.csv)",
                        type=CustomerType.both, status=CustomerStatus.active)
        db.add(cust)
        db.flush()
    return cust


def _get_or_create_location(db, cache, postal: str, country: str) -> Location:
    key = (postal.strip().upper(), country)
    if key in cache:
        return cache[key]
    existing = db.scalar(
        select(Location).where(Location.postal_zip == postal.strip().upper(), Location.country == country)
    )
    if existing is None:
        existing = Location(name=f"{postal.strip().upper()} ({country})", type=LocationType.customer_site,
                            postal_zip=postal.strip().upper(), country=country)
        db.add(existing)
        db.flush()
    cache[key] = existing
    return existing


def _next_probill_base(db) -> int:
    from sqlalchemy import func
    return int(db.scalar(select(func.count()).select_from(Shipment)) or 0)


def import_orders(path: str = DEFAULT_CSV) -> None:
    db = SessionLocal()
    loc_cache: dict = {}
    created = 0
    try:
        cust = _get_or_create_customer(db)
        seq = _next_probill_base(db)

        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                flags: list[dict] = []

                o_country, o_noncanon = _norm_country(row.get("origin_country", ""))
                d_country, d_noncanon = _norm_country(row.get("dest_country", ""))
                if o_noncanon or d_noncanon:
                    flags.append({"code": "COUNTRY_NONCANONICAL",
                                  "detail": f"origin='{row.get('origin_country')}' dest='{row.get('dest_country')}'",
                                  "at": datetime.now(timezone.utc).isoformat()})

                origin_zip = (row.get("origin_zip") or "").strip()
                dest_zip = (row.get("dest_zip") or "").strip()
                for label, z, country in (("origin", origin_zip, o_country), ("dest", dest_zip, d_country)):
                    ok = (country == "US" and US_ZIP.match(z)) or (country == "CA" and CA_POSTAL.match(z))
                    if z and not ok:
                        flags.append({"code": "BAD_POSTAL", "detail": f"{label}_zip='{z}' country={country}",
                                      "at": datetime.now(timezone.utc).isoformat()})

                shipper = _get_or_create_location(db, loc_cache, origin_zip or "UNKNOWN", o_country or "US")
                consignee = _get_or_create_location(db, loc_cache, dest_zip or "UNKNOWN", d_country or "US")

                # Quote handling.
                quote_raw = (row.get("Quote") or "").strip()
                quote_num = None
                if quote_raw:
                    m = re.search(r"[-+]?\d*\.?\d+", quote_raw.replace(",", ""))
                    if m:
                        quote_num = float(m.group())
                    else:
                        flags.append({"code": "QUOTE_UNPARSEABLE", "detail": f"Quote='{quote_raw}'",
                                      "at": datetime.now(timezone.utc).isoformat()})

                try:
                    weight = float(row.get("weight_lbs") or 0)
                except ValueError:
                    weight = 0.0

                seq += 1
                shipment = Shipment(
                    probill_number=f"P{seq:07d}",
                    customer_id=cust.id,
                    shipper_location_id=shipper.id,
                    consignee_location_id=consignee.id,
                    total_weight_lbs=weight,
                    freight_class=(row.get("freight_class") or "").strip(),
                    stackable=_to_bool(row.get("is_stackable")),
                    is_urgent=_to_bool(row.get("is_urgent")),
                    is_cross_border=(o_country != d_country),
                    customer_reference=(row.get("shipment_id") or "").strip(),
                    source=ShipmentSource.import_,
                    created_by="import",
                    data_quality_flags=flags,
                )
                if quote_num is not None:
                    shipment.po_numbers = [f"quote:{quote_num}"]
                db.add(shipment)
                db.flush()

                # Handling unit from skid_dims when parseable.
                dims_raw = (row.get("skid_dims") or "").strip()
                dm = DIMS.match(dims_raw)
                if dm:
                    db.add(HandlingUnit(
                        shipment_id=shipment.id, type=HandlingUnitType.skid, quantity=1,
                        length_in=float(dm.group(1)), width_in=float(dm.group(2)), height_in=float(dm.group(3)),
                        weight_lbs=weight, stackable=shipment.stackable,
                    ))
                elif dims_raw and dims_raw.lower() != "unknown":
                    flags2 = list(shipment.data_quality_flags)
                    flags2.append({"code": "DIMS_UNPARSEABLE", "detail": f"skid_dims='{dims_raw}'",
                                   "at": datetime.now(timezone.utc).isoformat()})
                    shipment.data_quality_flags = flags2
                else:
                    flags2 = list(shipment.data_quality_flags)
                    flags2.append({"code": "DIMS_UNKNOWN", "detail": "no usable skid dimensions",
                                   "at": datetime.now(timezone.utc).isoformat()})
                    shipment.data_quality_flags = flags2

                created += 1

        db.commit()
        print(f"Imported {created} shipments from {os.path.abspath(path)}")
    finally:
        db.close()


if __name__ == "__main__":
    import_orders(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV)
