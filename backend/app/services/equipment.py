"""Telematics device attachment rule.

A device may be attached to only one asset at a time. Attaching a device to a new
asset detaches it from whatever it was on. This logic is centralized here so it
is easy to audit once Batch 4's audit_log exists.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import APIError
from app.models.audit import AuditAction
from app.models.equipment import (
    AttachedToType,
    DeviceStatus,
    TelematicsDevice,
    Tractor,
    Trailer,
)
from app.services.audit import record_audit


def _asset_model(asset_type: AttachedToType):
    return Tractor if asset_type == AttachedToType.tractor else Trailer


def attach_device(db: Session, device_id: int, asset_type: AttachedToType, asset_id: int) -> None:
    """Attach ``device_id`` to (asset_type, asset_id), detaching any prior holder."""
    device = db.get(TelematicsDevice, device_id)
    if device is None:
        raise APIError(422, "INVALID_REFERENCE", "telematics_device_id does not exist.",
                       {"field": "telematics_device_id", "value": device_id})

    # If the device is on another asset, clear that asset's pointer first.
    if device.attached_to_type != AttachedToType.none and device.attached_to_id is not None:
        prior_model = _asset_model(device.attached_to_type)
        prior = db.get(prior_model, device.attached_to_id)
        if prior is not None and prior.id != asset_id:
            prior.telematics_device_id = None
            record_audit(db, entity_type="telematics_devices", entity_id=device.id,
                         action=AuditAction.detach,
                         reason=f"Detached from {device.attached_to_type.value} {prior.id}")

    # If the target asset already had a different device, unassign that one.
    target = db.get(_asset_model(asset_type), asset_id)
    if target is not None and target.telematics_device_id not in (None, device_id):
        old = db.get(TelematicsDevice, target.telematics_device_id)
        if old is not None:
            old.attached_to_type = AttachedToType.none
            old.attached_to_id = None
            old.status = DeviceStatus.unassigned
            record_audit(db, entity_type="telematics_devices", entity_id=old.id,
                         action=AuditAction.detach,
                         reason=f"Replaced on {asset_type.value} {asset_id}")

    device.attached_to_type = asset_type
    device.attached_to_id = asset_id
    device.status = DeviceStatus.active
    record_audit(db, entity_type="telematics_devices", entity_id=device.id,
                 action=AuditAction.attach,
                 reason=f"Attached to {asset_type.value} {asset_id}")


def detach_device_from_asset(db: Session, asset_type: AttachedToType, asset_id: int) -> None:
    """If any device is attached to this asset, mark it unassigned."""
    device = db.scalar(
        select(TelematicsDevice).where(
            TelematicsDevice.attached_to_type == asset_type,
            TelematicsDevice.attached_to_id == asset_id,
        )
    )
    if device is not None:
        device.attached_to_type = AttachedToType.none
        device.attached_to_id = None
        device.status = DeviceStatus.unassigned
        record_audit(db, entity_type="telematics_devices", entity_id=device.id,
                     action=AuditAction.detach,
                     reason=f"Detached from {asset_type.value} {asset_id}")
