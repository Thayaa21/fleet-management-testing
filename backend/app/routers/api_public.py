"""Public customer API (/api/v1). Secured by API keys via the api_auth pipeline.

Every response — success or failure — is logged to api_request_log. Handlers log
their own success completion; the api_auth dependency logs rejections.
"""
import json

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.api import ApiErrorCode, IdempotencyKey
from app.models.location import Location
from app.models.milestone import Milestone
from app.models.shipment import Shipment, ShipmentSource
from app.schemas.api_public import PublicPickupCreate, PublicShipmentCreate
from app.services.api_gateway import AuthContext, api_auth, log_api_request

router = APIRouter(prefix="/api/v1", tags=["public-api"])


def _log_ok(db, request, ctx: AuthContext, status: int, body: dict | None = None):
    log_api_request(db, request, status=status, error_code=None, client_id=ctx.client.id,
                    key_prefix=ctx.key.key_prefix, body=body, started=getattr(request.state, "api_started", 0))


def _city_position(db: Session, shipment: Shipment) -> str | None:
    """City-level last-known position only — never raw GPS to customers."""
    loc_id = shipment.current_location_id
    if loc_id is None:
        return None
    loc = db.get(Location, loc_id)
    if loc is None:
        return None
    parts = [p for p in [loc.city, loc.province_state, loc.country] if p]
    return ", ".join(parts) or None


def _tracking_response(db: Session, shipment: Shipment) -> dict:
    milestones = db.scalars(
        select(Milestone).where(Milestone.shipment_id == shipment.id, Milestone.is_voided.is_(False))
        .order_by(Milestone.event_at)
    ).all()
    return {
        "probill_number": shipment.probill_number,
        "status": shipment.current_status.value,
        "eta": shipment.estimated_delivery_at.isoformat() if shipment.estimated_delivery_at else None,
        "last_known_position": _city_position(db, shipment),
        "milestones": [
            {"event_code": m.event_code.value,
             "event_at": m.event_at.isoformat() if m.event_at else None,
             "edi_214_code": m.edi_214_code}
            for m in milestones
        ],
    }


@router.get("/tracking/{probill_number}")
def track_by_probill(probill_number: str, request: Request,
                     ctx: AuthContext = Depends(api_auth("tracking:read")), db: Session = Depends(get_db)):
    shipment = db.scalar(
        select(Shipment).where(
            Shipment.probill_number == probill_number.strip().upper(),
            Shipment.customer_id == ctx.customer_id,
        )
    )
    if shipment is None:
        log_api_request(db, request, status=404, error_code=ApiErrorCode.UNKNOWN_PROBILL,
                        client_id=ctx.client.id, key_prefix=ctx.key.key_prefix, body=None,
                        started=getattr(request.state, "api_started", 0))
        raise APIError(404, "UNKNOWN_PROBILL", f"No shipment {probill_number} for your account.")
    resp = _tracking_response(db, shipment)
    _log_ok(db, request, ctx, 200)
    return resp


@router.get("/tracking")
def track_by_reference(request: Request, po_number: str | None = None, bol_number: str | None = None,
                       ctx: AuthContext = Depends(api_auth("tracking:read")), db: Session = Depends(get_db)):
    stmt = select(Shipment).where(Shipment.customer_id == ctx.customer_id)
    if bol_number:
        stmt = stmt.where(Shipment.bol_number == bol_number)
    shipment = None
    for s in db.scalars(stmt):
        if po_number and po_number not in (s.po_numbers or []):
            continue
        shipment = s
        break
    if shipment is None:
        log_api_request(db, request, status=404, error_code=ApiErrorCode.UNKNOWN_PROBILL,
                        client_id=ctx.client.id, key_prefix=ctx.key.key_prefix, body=None,
                        started=getattr(request.state, "api_started", 0))
        raise APIError(404, "UNKNOWN_PROBILL", "No matching shipment for your account.")
    resp = _tracking_response(db, shipment)
    _log_ok(db, request, ctx, 200)
    return resp


def _check_idempotency(db, ctx, key: str | None):
    if not key:
        return None
    row = db.scalar(select(IdempotencyKey).where(
        IdempotencyKey.api_client_id == ctx.client.id, IdempotencyKey.idempotency_key == key))
    return row


def _store_idempotency(db, ctx, key: str | None, status: int, body: dict):
    if not key:
        return
    db.add(IdempotencyKey(api_client_id=ctx.client.id, idempotency_key=key,
                          response_status=status, response_body=body))
    db.commit()


def _next_probill(db: Session) -> str:
    from sqlalchemy import func
    n = db.scalar(func.count(Shipment.id)) or 0
    return f"P{n + 1:07d}"


@router.post("/shipments", status_code=201)
def book_shipment(body: PublicShipmentCreate, request: Request,
                  idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
                  ctx: AuthContext = Depends(api_auth("shipments:write")), db: Session = Depends(get_db)):
    prior = _check_idempotency(db, ctx, idempotency_key)
    if prior is not None:
        log_api_request(db, request, status=prior.response_status, error_code=ApiErrorCode.DUPLICATE_REQUEST,
                        client_id=ctx.client.id, key_prefix=ctx.key.key_prefix, body=None,
                        started=getattr(request.state, "api_started", 0))
        return prior.response_body

    shipment = Shipment(
        probill_number=_next_probill(db),
        customer_id=ctx.customer_id,
        bol_number=body.bol_number,
        total_weight_lbs=body.total_weight_lbs,
        freight_class=body.freight_class,
        pickup_date=body.pickup_date,
        po_numbers=body.po_numbers,
        customer_reference=body.customer_reference,
        is_cross_border=(body.shipper_country.upper() != body.consignee_country.upper()),
        source=ShipmentSource.api,
        created_by=f"api_client:{ctx.client.id}",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    resp = {"probill_number": shipment.probill_number, "status": shipment.current_status.value, "id": shipment.id}
    _store_idempotency(db, ctx, idempotency_key, 201, resp)
    _log_ok(db, request, ctx, 201, body=json.loads(body.model_dump_json()))
    return resp


@router.post("/pickups", status_code=201)
def request_pickup(body: PublicPickupCreate, request: Request,
                   idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
                   ctx: AuthContext = Depends(api_auth("pickups:write")), db: Session = Depends(get_db)):
    from app.models.operations import PickupChannel, PickupRequest

    prior = _check_idempotency(db, ctx, idempotency_key)
    if prior is not None:
        log_api_request(db, request, status=prior.response_status, error_code=ApiErrorCode.DUPLICATE_REQUEST,
                        client_id=ctx.client.id, key_prefix=ctx.key.key_prefix, body=None,
                        started=getattr(request.state, "api_started", 0))
        return prior.response_body

    pickup = PickupRequest(
        customer_id=ctx.customer_id,
        requested_date=body.requested_date,
        expected_pieces=body.expected_pieces,
        expected_weight_lbs=body.expected_weight_lbs,
        notes=body.notes,
        created_via=PickupChannel.api,
    )
    db.add(pickup)
    db.commit()
    db.refresh(pickup)
    resp = {"pickup_id": pickup.id, "status": pickup.status.value}
    _store_idempotency(db, ctx, idempotency_key, 201, resp)
    _log_ok(db, request, ctx, 201, body=json.loads(body.model_dump_json()))
    return resp
