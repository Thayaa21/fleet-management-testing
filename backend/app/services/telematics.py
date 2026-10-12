"""Telematics ingestion.

Rule: never drop an event silently. Every ping in a batch produces exactly one
telematics_ingest_log row (success or a specific error_code). A bad provider
secret is a hard 401 (with an AUTH_FAILED log row) and no pings are processed.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import APIError
from app.models.equipment import AttachedToType, DeviceStatus, TelematicsDevice
from app.models.telematics import GpsPing, IngestErrorCode, TelematicsIngestLog
from app.services.geofence import maybe_geofence_arrival

settings = get_settings()


def _parse_dt(value) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _log(db: Session, *, provider, http_status, device_serial, resolved_device_id, error_code, payload):
    db.add(TelematicsIngestLog(
        provider=provider, http_status_returned=http_status, device_serial=device_serial,
        resolved_device_id=resolved_device_id, error_code=error_code, raw_payload=payload,
    ))


def ingest_batch(db: Session, provider: str, secret_header: str | None, pings: list[dict]) -> dict:
    provider = (provider or "").strip().lower()
    expected = settings.telematics_secret_map.get(provider)

    # ── Auth: hard 401, one log row, nothing processed. ──
    if expected is None or secret_header != expected:
        _log(db, provider=provider, http_status=401, device_serial=None,
             resolved_device_id=None, error_code=IngestErrorCode.AUTH_FAILED, payload=None)
        db.commit()
        raise APIError(401, "AUTH_FAILED", "Invalid telematics secret for provider.", {"provider": provider})

    summary = {"accepted": 0, "rejected": 0, "by_error": {}}

    def bump(code: IngestErrorCode | None):
        if code is None:
            summary["accepted"] += 1
        else:
            summary["rejected"] += 1
            summary["by_error"][code.value] = summary["by_error"].get(code.value, 0) + 1

    for ping in pings or []:
        serial = str(ping.get("device_serial") or "").strip().upper() or None
        recorded_at = _parse_dt(ping.get("recorded_at"))
        lat, lng = ping.get("lat"), ping.get("lng")

        # Malformed.
        if not serial or recorded_at is None or not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            _log(db, provider=provider, http_status=422, device_serial=serial,
                 resolved_device_id=None, error_code=IngestErrorCode.MALFORMED_PAYLOAD, payload=ping)
            bump(IngestErrorCode.MALFORMED_PAYLOAD)
            continue

        device = db.scalar(select(TelematicsDevice).where(TelematicsDevice.device_serial == serial))
        if device is None:
            _log(db, provider=provider, http_status=404, device_serial=serial,
                 resolved_device_id=None, error_code=IngestErrorCode.UNKNOWN_DEVICE, payload=ping)
            bump(IngestErrorCode.UNKNOWN_DEVICE)
            continue

        # Unassigned: device not attached to an asset (we can't place the ping).
        if device.attached_to_type == AttachedToType.none or device.attached_to_id is None \
                or device.status in (DeviceStatus.unassigned, DeviceStatus.inactive):
            _log(db, provider=provider, http_status=409, device_serial=serial,
                 resolved_device_id=device.id, error_code=IngestErrorCode.DEVICE_UNASSIGNED, payload=ping)
            bump(IngestErrorCode.DEVICE_UNASSIGNED)
            continue

        # Dedupe on (device_id, recorded_at).
        dup = db.scalar(
            select(GpsPing).where(GpsPing.device_id == device.id, GpsPing.recorded_at == recorded_at)
        )
        if dup is not None:
            _log(db, provider=provider, http_status=200, device_serial=serial,
                 resolved_device_id=device.id, error_code=IngestErrorCode.DUPLICATE, payload=ping)
            bump(IngestErrorCode.DUPLICATE)
            continue

        # Store.
        db.add(GpsPing(
            device_id=device.id, recorded_at=recorded_at, lat=float(lat), lng=float(lng),
            speed_kph=ping.get("speed_kph"), heading=ping.get("heading"),
            odometer_km=ping.get("odometer_km"), engine_on=ping.get("engine_on"), raw_payload=ping,
        ))
        if device.last_ping_at is None or (device.last_ping_at.replace(tzinfo=timezone.utc)
                                           if device.last_ping_at.tzinfo is None else device.last_ping_at) < recorded_at:
            device.last_ping_at = recorded_at
        _log(db, provider=provider, http_status=200, device_serial=serial,
             resolved_device_id=device.id, error_code=None, payload=ping)
        bump(None)

        maybe_geofence_arrival(db, device, float(lat), float(lng))

    db.commit()
    return summary
