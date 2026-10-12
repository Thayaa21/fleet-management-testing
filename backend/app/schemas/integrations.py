from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.api import ApiClientStatus, ApiErrorCode, WebhookError, WebhookSubStatus


# ── Clients ──
class ApiClientCreate(BaseModel):
    customer_id: int
    name: str


class ApiClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_id: int
    name: str
    status: ApiClientStatus


# ── Keys ──
class ApiKeyCreate(BaseModel):
    scopes: list[str] = []
    expires_at: datetime | None = None


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    api_client_id: int
    key_prefix: str
    scopes: list[str]
    expires_at: datetime | None
    last_used_at: datetime | None
    revoked_at: datetime | None


class ApiKeyCreated(ApiKeyOut):
    # Returned ONCE at creation with the full key.
    api_key: str


# ── IP allowlist ──
class IpAllowlistCreate(BaseModel):
    cidr: str
    label: str = ""


class IpAllowlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    api_client_id: int
    cidr: str
    label: str


# ── Webhook subscriptions ──
class WebhookSubCreate(BaseModel):
    target_url: str
    event_types: list[str] = []
    secret: str = ""


class WebhookSubOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    api_client_id: int
    target_url: str
    event_types: list[str]
    status: WebhookSubStatus
    consecutive_failures: int


# ── Logs & deliveries ──
class ApiLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    request_id: str | None
    received_at: datetime
    api_client_id: int | None
    key_prefix: str | None
    source_ip: str | None
    method: str
    path: str
    response_status: int
    error_code: ApiErrorCode | None
    latency_ms: int


class WebhookDeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subscription_id: int
    shipment_id: int | None
    attempt_number: int
    sent_at: datetime | None
    response_status: int | None
    error: WebhookError | None
    delivered: bool
    next_retry_at: datetime | None
