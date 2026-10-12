"""Standard error envelope used by every endpoint.

Shape: {"error": {"code": "...", "message": "...", "details": {...}}}
"""
from typing import Any

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
