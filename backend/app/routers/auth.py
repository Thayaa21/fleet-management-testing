"""Authentication endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserOut
from app.services.auth import get_current_user, require_staff
from app.services.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise APIError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")
    if not user.is_active:
        raise APIError(403, "ACCOUNT_INACTIVE", "This account is inactive.")

    token = create_access_token(subject=str(user.id), extra={"role": user.role.value})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.get("/staff-check")
def staff_check(user: User = Depends(require_staff)) -> dict:
    """Minimal staff-only endpoint used to exercise role enforcement.

    Real staff endpoints arrive in Batch 3; this exists so authorization is
    testable now (a customer_user calling it must receive 403).
    """
    return {"ok": True, "role": user.role.value}
