from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.audit import ActorType, AuditAction


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int
    action: AuditAction
    changed_fields: dict | None
    actor_type: ActorType
    actor_id: str | None
    reason: str | None
    request_id: str | None
    created_at: datetime
