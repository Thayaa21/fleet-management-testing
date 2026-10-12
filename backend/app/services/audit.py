"""Audit logging.

Two paths write audit rows:

1. Automatic ORM hook (before_flush): for INSERT/UPDATE/DELETE on audited models,
   an AuditLog row is staged capturing per-field [old, new] changes.
2. Explicit domain calls: record_audit(...) for actions that aren't plain field
   diffs (milestone void, device attach/detach, shipment cancel).

The current actor and request id come from contextvars set per request by a
FastAPI dependency (set_audit_context). Outside a request (scripts, tests) the
actor defaults to system.
"""
from contextvars import ContextVar
from datetime import datetime, timezone

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from app.models.audit import ActorType, AuditAction, AuditLog

# ── Request-scoped actor context ──────────────────────────
_actor_type: ContextVar[str] = ContextVar("actor_type", default=ActorType.system.value)
_actor_id: ContextVar[str | None] = ContextVar("actor_id", default=None)
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

# Models that are audited automatically. Kept as string table names to avoid
# import cycles; the hook checks __tablename__.
AUDITED_TABLES = {
    "shipments",
    "milestones",
    "handling_units",
    "tractors",
    "trailers",
    "telematics_devices",
}

# Never audit these (avoids recursion / noise).
_NEVER_AUDIT = {"audit_log", "alembic_version", "users"}


def set_audit_context(actor_type: str, actor_id: str | None, request_id: str | None) -> None:
    _actor_type.set(actor_type)
    _actor_id.set(actor_id)
    _request_id.set(request_id)


def reset_audit_context() -> None:
    _actor_type.set(ActorType.system.value)
    _actor_id.set(None)
    _request_id.set(None)


def _current_actor() -> tuple[str, str | None, str | None]:
    return _actor_type.get(), _actor_id.get(), _request_id.get()


def record_audit(
    session: Session,
    *,
    entity_type: str,
    entity_id: int,
    action: AuditAction,
    changed_fields: dict | None = None,
    reason: str | None = None,
) -> None:
    """Explicitly stage an audit row on the given session."""
    actor_type, actor_id, request_id = _current_actor()
    session.add(
        AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changed_fields=changed_fields,
            actor_type=ActorType(actor_type),
            actor_id=actor_id,
            reason=reason,
            request_id=request_id,
            created_at=datetime.now(timezone.utc),
        )
    )


def _diff(obj) -> dict:
    """Per-field {field: [old, new]} for a dirty object's committed changes."""
    changes: dict = {}
    state = inspect(obj)
    for attr in state.attrs:
        hist = attr.history
        if not hist.has_changes():
            continue
        old = hist.deleted[0] if hist.deleted else None
        new = hist.added[0] if hist.added else None
        if old == new:
            continue
        changes[attr.key] = [_json_safe(old), _json_safe(new)]
    return changes


def _json_safe(v):
    if isinstance(v, datetime):
        return v.isoformat()
    if hasattr(v, "value"):  # Enum
        return v.value
    return v


_PENDING_KEY = "_pending_audit_creates"


def _auto_audit_before_flush(session: Session, flush_context, instances) -> None:
    """Stage audit rows for UPDATE and DELETE (ids already known), and remember
    INSERTs so their audit rows can be added after ids are assigned."""
    actor_type, actor_id, request_id = _current_actor()

    def make(entity_type, entity_id, action, changed):
        return AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changed_fields=changed,
            actor_type=ActorType(actor_type),
            actor_id=actor_id,
            reason=None,
            request_id=request_id,
            created_at=datetime.now(timezone.utc),
        )

    rows: list[AuditLog] = []

    for obj in session.dirty:
        table = getattr(obj, "__tablename__", None)
        if table in AUDITED_TABLES and session.is_modified(obj, include_collections=False):
            changes = _diff(obj)
            if changes:
                rows.append(make(table, obj.id, AuditAction.update, changes))

    for obj in session.deleted:
        table = getattr(obj, "__tablename__", None)
        if table in AUDITED_TABLES:
            rows.append(make(table, obj.id, AuditAction.delete, None))

    for row in rows:
        session.add(row)

    # Remember creates; their ids are assigned during this flush.
    pending = [obj for obj in session.new if getattr(obj, "__tablename__", None) in AUDITED_TABLES]
    if pending:
        existing = getattr(session, _PENDING_KEY, [])
        setattr(session, _PENDING_KEY, existing + pending)


def _auto_audit_after_flush(session: Session, flush_context) -> None:
    """After ids are assigned, add create-audit rows for remembered INSERTs.
    Adding rows here schedules them for the next flush within the same commit."""
    pending = getattr(session, _PENDING_KEY, None)
    if not pending:
        return
    setattr(session, _PENDING_KEY, [])
    actor_type, actor_id, request_id = _current_actor()
    for obj in pending:
        session.add(
            AuditLog(
                entity_type=obj.__tablename__,
                entity_id=obj.id,
                action=AuditAction.create,
                changed_fields=None,
                actor_type=ActorType(actor_type),
                actor_id=actor_id,
                reason=None,
                request_id=request_id,
                created_at=datetime.now(timezone.utc),
            )
        )


def register_audit_listeners(session_factory) -> None:
    """Attach the audit hooks to a sessionmaker/Session class."""
    event.listen(session_factory, "before_flush", _auto_audit_before_flush)
    event.listen(session_factory, "after_flush", _auto_audit_after_flush)
