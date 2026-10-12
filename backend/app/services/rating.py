"""LTL rating.

Charge = max(weight_cwt * rate_per_cwt, minimum_charge), where the rate is chosen
by lane (origin/dest terminal), the weight break the shipment falls into, and its
freight class. Fuel surcharge is a percent of the freight charge (by effective
date). Accessorials add flat or per-hour charges. Returns a line-item breakdown.
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.billing import Accessorial, FuelSurcharge, RateTable, ShipmentAccessorial
from app.models.shipment import Shipment


def _find_rate(db: Session, origin_id: int | None, dest_id: int | None, weight: float, freight_class: str) -> RateTable | None:
    stmt = select(RateTable).where(RateTable.freight_class == freight_class)
    # Prefer an exact lane match, then fall back to a generic (null lane) table.
    lane_match = db.scalars(
        stmt.where(RateTable.origin_terminal_id == origin_id, RateTable.destination_terminal_id == dest_id)
    ).all()
    candidates = lane_match or db.scalars(
        select(RateTable).where(
            RateTable.freight_class == freight_class,
            RateTable.origin_terminal_id.is_(None),
            RateTable.destination_terminal_id.is_(None),
        )
    ).all()
    for rt in candidates:
        if weight >= rt.weight_break_min and (rt.weight_break_max is None or weight < rt.weight_break_max):
            return rt
    return None


def _fuel_percent(db: Session, on: date) -> float:
    row = db.scalar(
        select(FuelSurcharge).where(FuelSurcharge.effective_date <= on).order_by(FuelSurcharge.effective_date.desc())
    )
    return row.percent if row else 0.0


def rate_shipment(db: Session, shipment: Shipment) -> dict:
    """Return {line_items, subtotal, fuel_surcharge, accessorials_total, total}."""
    weight = shipment.total_weight_lbs or 0.0
    cwt = weight / 100.0
    freight_class = shipment.freight_class or "100"

    line_items = []
    rt = _find_rate(db, shipment.shipper_location_id, shipment.consignee_location_id, weight, freight_class)
    if rt is None:
        freight_charge = 0.0
        line_items.append({"code": "FREIGHT", "description": "No rate on file for this lane/class", "amount": 0.0})
    else:
        computed = round(cwt * rt.rate_per_cwt, 2)
        freight_charge = max(computed, rt.minimum_charge)
        applied_min = freight_charge > computed
        line_items.append({
            "code": "FREIGHT",
            "description": f"{weight:.0f} lbs @ {rt.rate_per_cwt}/cwt class {freight_class}"
                           + (" (minimum applied)" if applied_min else ""),
            "amount": round(freight_charge, 2),
        })

    # Accessorials.
    accessorials_total = 0.0
    for sa in db.scalars(select(ShipmentAccessorial).where(ShipmentAccessorial.shipment_id == shipment.id)):
        acc = db.get(Accessorial, sa.accessorial_id)
        if acc is None:
            continue
        amount = round(acc.charge * (sa.quantity if acc.per_hour else 1), 2)
        accessorials_total += amount
        line_items.append({"code": acc.code, "description": acc.name, "amount": amount})

    fuel_pct = _fuel_percent(db, shipment.pickup_date or date.today())
    fuel = round(freight_charge * fuel_pct / 100.0, 2)
    if fuel:
        line_items.append({"code": "FUEL", "description": f"Fuel surcharge {fuel_pct}%", "amount": fuel})

    subtotal = round(freight_charge + accessorials_total, 2)
    total = round(subtotal + fuel, 2)
    return {
        "line_items": line_items,
        "subtotal": subtotal,
        "fuel_surcharge": fuel,
        "accessorials_total": round(accessorials_total, 2),
        "total": total,
    }
