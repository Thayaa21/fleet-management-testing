"""API key generation and verification.

Full key format: `tms_<prefix8>_<secret32>`. Only the prefix (for display/lookup)
and a sha256 hash of the full key are stored — never the raw key after creation.
"""
import hashlib
import secrets
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.api import ApiKey


def _hash(full_key: str) -> str:
    return hashlib.sha256(full_key.encode("utf-8")).hexdigest()


def generate_key() -> tuple[str, str, str]:
    """Return (full_key, prefix, key_hash)."""
    prefix = secrets.token_hex(4)  # 8 hex chars
    secret = secrets.token_hex(16)  # 32 hex chars
    full = f"tms_{prefix}_{secret}"
    return full, prefix, _hash(full)


def create_api_key(db: Session, api_client_id: int, scopes: list[str], expires_at: datetime | None) -> tuple[ApiKey, str]:
    """Create an ApiKey; returns (row, full_key). The full key is returned ONCE."""
    full, prefix, key_hash = generate_key()
    row = ApiKey(api_client_id=api_client_id, key_prefix=prefix, key_hash=key_hash,
                 scopes=scopes, expires_at=expires_at)
    db.add(row)
    db.flush()
    return row, full


def verify_key(db: Session, presented: str) -> ApiKey | None:
    """Resolve a presented full key to its ApiKey row (or None)."""
    if not presented or not presented.startswith("tms_"):
        return None
    parts = presented.split("_")
    if len(parts) != 3:
        return None
    prefix = parts[1]
    candidate_hash = _hash(presented)
    row = db.query(ApiKey).filter(ApiKey.key_prefix == prefix).first()
    if row is None or row.key_hash != candidate_hash:
        return None
    return row
