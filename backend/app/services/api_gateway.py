"""Customer API gateway: authentication pipeline, request logging, rate limiting.

Implemented as a FastAPI dependency (`api_auth(scope)`) rather than pure ASGI
middleware, so each route declares the scope it needs. The pipeline order is:

  request id → (log written at the end) → API key present → resolve key →
  revoked? → expired? → client active? → IP allowlist → scope → rate limit.

Every request — accepted or rejected — writes exactly one api_request_log row via
`log_api_request`. Rejections raise APIError, which the shared error handlers turn
into the standard envelope; a small wrapper ensures the log row is still written.
"""
import ipaddress
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.api import ApiClient, ApiClientStatus, ApiErrorCode, ApiKey, ApiRequestLog, IpAllowlist
from app.services.api_keys import verify_key

RATE_LIMIT_MAX = 120          # requests
RATE_LIMIT_WINDOW_S = 60      # per minute, per key prefix
_BUCKETS: dict[str, deque] = defaultdict(deque)


@dataclass
class AuthContext:
    client: ApiClient
    key: ApiKey
    scopes: list[str]
    customer_id: int


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("X-Forwarded-For")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _redact(body: dict | None) -> dict | None:
    if not isinstance(body, dict):
        return body
    redacted = {}
    for k, v in body.items():
        if k.lower() in ("secret", "api_key", "x-api-key", "password"):
            redacted[k] = "***redacted***"
        else:
            redacted[k] = v
    return redacted


def log_api_request(db: Session, request: Request, *, status: int, error_code: ApiErrorCode | None,
                    client_id: int | None, key_prefix: str | None, body: dict | None, started: float) -> None:
    row = ApiRequestLog(
        request_id=getattr(request.state, "request_id", None),
        api_client_id=client_id,
        key_prefix=key_prefix,
        source_ip=_client_ip(request),
        method=request.method,
        path=request.url.path,
        query=str(request.url.query or ""),
        request_body=_redact(body),
        response_status=status,
        error_code=error_code,
        latency_ms=int((time.perf_counter() - started) * 1000),
        user_agent=request.headers.get("User-Agent", "")[:255],
    )
    db.add(row)
    db.commit()


def _rate_limited(prefix: str) -> bool:
    now = time.monotonic()
    bucket = _BUCKETS[prefix]
    while bucket and bucket[0] < now - RATE_LIMIT_WINDOW_S:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX:
        return True
    bucket.append(now)
    return False


def _ip_allowed(db: Session, client_id: int, ip: str) -> bool:
    rules = list(db.scalars(select(IpAllowlist).where(IpAllowlist.api_client_id == client_id)))
    if not rules:
        return True  # no allowlist configured → allow all
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for r in rules:
        try:
            if addr in ipaddress.ip_network(r.cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


def api_auth(required_scope: str):
    """Dependency factory enforcing the full pipeline for a given scope."""

    def _dep(request: Request, db: Session = Depends(get_db)) -> AuthContext:
        started = time.perf_counter()

        def fail(code: ApiErrorCode, http: int, message: str, *, client_id=None, prefix=None, details=None):
            log_api_request(db, request, status=http, error_code=code, client_id=client_id,
                            key_prefix=prefix, body=None, started=started)
            raise APIError(http, code.value, message, details)

        presented = request.headers.get("X-API-Key")
        if not presented:
            fail(ApiErrorCode.MISSING_API_KEY, 401, "Missing X-API-Key header.")

        key = verify_key(db, presented)
        prefix = presented.split("_")[1] if presented and presented.count("_") == 2 else None
        if key is None:
            fail(ApiErrorCode.INVALID_API_KEY, 401, "API key is not valid.", prefix=prefix)

        if key.revoked_at is not None:
            fail(ApiErrorCode.REVOKED_API_KEY, 401,
                 f"API key {key.key_prefix} was revoked. Generate a new key in the portal.",
                 client_id=key.api_client_id, prefix=key.key_prefix)

        exp = _aware(key.expires_at)
        if exp is not None and exp < _now():
            fail(ApiErrorCode.EXPIRED_API_KEY, 401,
                 f"API key {key.key_prefix} expired on {exp.isoformat()}. Generate a new key in the portal.",
                 client_id=key.api_client_id, prefix=key.key_prefix)

        client = db.get(ApiClient, key.api_client_id)
        if client is None or client.status != ApiClientStatus.active:
            fail(ApiErrorCode.INVALID_API_KEY, 401, "API client is not active.",
                 client_id=key.api_client_id, prefix=key.key_prefix)

        ip = _client_ip(request)
        if not _ip_allowed(db, client.id, ip):
            fail(ApiErrorCode.IP_NOT_ALLOWED, 403,
                 f"Request from {ip} is not in the allowlist for client {client.name}.",
                 client_id=client.id, prefix=key.key_prefix)

        if required_scope not in (key.scopes or []):
            fail(ApiErrorCode.INSUFFICIENT_SCOPE, 403,
                 f"This key lacks the required scope '{required_scope}'.",
                 client_id=client.id, prefix=key.key_prefix,
                 details={"required_scope": required_scope, "granted": key.scopes})

        if _rate_limited(key.key_prefix):
            fail(ApiErrorCode.RATE_LIMITED, 429, "Rate limit exceeded. Slow down and retry shortly.",
                 client_id=client.id, prefix=key.key_prefix)

        key.last_used_at = _now()
        db.commit()

        # Stash for the route to log success at completion.
        request.state.api_ctx = AuthContext(client=client, key=key, scopes=list(key.scopes or []),
                                             customer_id=client.customer_id)
        request.state.api_started = started
        return request.state.api_ctx

    return _dep
