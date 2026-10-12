"""Importer smoke test: dirty rows are imported and flagged, not dropped."""
import csv

from sqlalchemy import select

from app.import_orders import import_orders
from app.models.shipment import Shipment


def test_import_flags_dirty_data(db_session, tmp_path, monkeypatch):
    # Point the importer's SessionLocal at the test session.
    import app.import_orders as mod
    monkeypatch.setattr(mod, "SessionLocal", lambda: db_session)
    # Don't let the importer close the shared test session.
    monkeypatch.setattr(db_session, "close", lambda: None)

    csv_path = tmp_path / "orders.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "shipment_id", "origin_zip", "dest_zip", "weight_lbs", "status", "freight_class",
            "base_rate_per_mile_cwt", "fuel_surcharge_percent", "accessorial_charges", "driver_id",
            "vendor_id", "created_at", "last_updated_timestamp", "skid_details", "is_stackable",
            "is_urgent", "delivery_appointment", "origin_country", "dest_country", "Quote", "skid_dims",
        ])
        # Clean US->CA cross-border row with parseable dims + quote.
        w.writerow(["SHP1", "85001", "L5R1S3", "1500", "pending", "92", "0.1", "20", "35", "", "",
                    "2025-07-07T22:25:39", "2025-07-08", "", "True", "False", "True",
                    "USA", "Canada", "$4228", "100x43x52"])
        # Dirty row: bad dest zip, unknown dims, blank quote.
        w.writerow(["SHP2", "85001", "285347", "250", "pending", "92", "0.1", "20", "35", "", "",
                    "2025-07-08T11:46:17", "2025-09-13", "", "False", "True", "True",
                    "US", "US", "", "unknown"])

    import_orders(str(csv_path))

    shipments = list(db_session.scalars(select(Shipment)))
    assert len(shipments) == 2

    by_ref = {s.customer_reference: s for s in shipments}
    s1, s2 = by_ref["SHP1"], by_ref["SHP2"]

    # Cross-border detected; non-canonical country flagged.
    assert s1.is_cross_border is True
    assert any(f["code"] == "COUNTRY_NONCANONICAL" for f in s1.data_quality_flags)

    # Bad postal + unknown dims flagged; row still imported.
    codes2 = {f["code"] for f in s2.data_quality_flags}
    assert "BAD_POSTAL" in codes2
    assert "DIMS_UNKNOWN" in codes2
