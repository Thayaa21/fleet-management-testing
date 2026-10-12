import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ApiClientStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"


class WebhookSubStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    failing = "failing"


class ApiErrorCode(str, enum.Enum):
    MISSING_API_KEY = "MISSING_API_KEY"
    INVALID_API_KEY = "INVALID_API_KEY"
    EXPIRED_API_KEY = "EXPIRED_API_KEY"
    REVOKED_API_KEY = "REVOKED_API_KEY"
    INSUFFICIENT_SCOPE = "INSUFFICIENT_SCOPE"
    IP_NOT_ALLOWED = "IP_NOT_ALLOWED"
    RATE_LIMITED = "RATE_LIMITED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNKNOWN_PROBILL = "UNKNOWN_PROBILL"
    UNKNOWN_EQUIPMENT_ID = "UNKNOWN_EQUIPMENT_ID"
    DUPLICATE_REQUEST = "DUPLICATE_REQUEST"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class WebhookError(str, enum.Enum):
    TIMEOUT = "TIMEOUT"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    HTTP_4XX = "HTTP_4XX"
    HTTP_5XX = "HTTP_5XX"
    AUTH_REJECTED = "AUTH_REJECTED"


class ApiClient(TimestampMixin, Base):
    __tablename__ = "api_clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ApiClientStatus] = mapped_column(
        Enum(ApiClientStatus, name="api_client_status"), default=ApiClientStatus.active, nullable=False
    )


class ApiKey(TimestampMixin, Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_client_id: Mapped[int] = mapped_column(ForeignKey("api_clients.id"), nullable=False, index=True)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IpAllowlist(Base):
    __tablename__ = "ip_allowlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_client_id: Mapped[int] = mapped_column(ForeignKey("api_clients.id"), nullable=False, index=True)
    cidr: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(120), default="")
    created_by: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class ApiRequestLog(Base):
    __tablename__ = "api_request_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)
    api_client_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    key_prefix: Mapped[str | None] = mapped_column(String(16), nullable=True)
    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    method: Mapped[str] = mapped_column(String(10), default="")
    path: Mapped[str] = mapped_column(String(255), default="")
    query: Mapped[str] = mapped_column(String(512), default="")
    request_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    response_status: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[ApiErrorCode | None] = mapped_column(
        Enum(ApiErrorCode, name="api_error_code"), nullable=True, index=True
    )
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    user_agent: Mapped[str] = mapped_column(String(255), default="")


class WebhookSubscription(TimestampMixin, Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_client_id: Mapped[int] = mapped_column(ForeignKey("api_clients.id"), nullable=False, index=True)
    target_url: Mapped[str] = mapped_column(String(500), nullable=False)
    event_types: Mapped[list] = mapped_column(JSON, default=list)
    secret: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[WebhookSubStatus] = mapped_column(
        Enum(WebhookSubStatus, name="webhook_sub_status"), default=WebhookSubStatus.active, nullable=False
    )
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("webhook_subscriptions.id"), nullable=False, index=True)
    shipment_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    milestone_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[WebhookError | None] = mapped_column(Enum(WebhookError, name="webhook_error"), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("api_client_id", "idempotency_key", name="uq_idempotency_client_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_client_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, default=200)
    response_body: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
