import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AuditAction(str, enum.Enum):
    create = "create"
    update = "update"
    void = "void"
    attach = "attach"
    detach = "detach"
    delete = "delete"
    cancel = "cancel"


class ActorType(str, enum.Enum):
    user = "user"
    system = "system"
    api_client = "api_client"
    agent = "agent"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="audit_action"), nullable=False)
    changed_fields: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    actor_type: Mapped[ActorType] = mapped_column(Enum(ActorType, name="actor_type"), default=ActorType.system, nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)
