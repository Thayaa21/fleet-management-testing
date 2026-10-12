"""Authentication and authorization dependencies.

- get_current_user: resolves the JWT bearer token to a User.
- require_role(...): dependency factory that enforces staff roles.
- scope_query_to_customer: shared helper so customer_user rows are always
  filtered to the caller's own customer_id (enforced in one place, not per
  endpoint).
"""
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.user import User, UserRole
from app.services.security import decode_access_token

# auto_error=False so we can return the standard error envelope ourselves.
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise APIError(401, "UNAUTHENTICATED", "Missing bearer token.")

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise APIError(401, "INVALID_TOKEN", "Token is invalid or expired.")

    sub = payload.get("sub")
    if sub is None:
        raise APIError(401, "INVALID_TOKEN", "Token is missing its subject.")

    user = db.get(User, int(sub))
    if user is None or not user.is_active:
        raise APIError(401, "INVALID_TOKEN", "User no longer exists or is inactive.")

    # Record the actor for the audit log for the rest of this request.
    from app.services.audit import set_audit_context  # local import to avoid cycle

    set_audit_context(actor_type="user", actor_id=str(user.id), request_id=getattr(request.state, "request_id", None))
    return user


def require_role(*roles: UserRole):
    """Dependency factory: allow only the given roles."""
    allowed = set(roles)

    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise APIError(
                403,
                "FORBIDDEN",
                "You do not have permission to access this resource.",
                {"required_roles": [r.value for r in allowed], "your_role": user.role.value},
            )
        return user

    return _dep


# Convenience: any internal staff role.
STAFF_ROLES = (UserRole.admin, UserRole.dispatcher, UserRole.dock)


def require_staff(user: User = Depends(get_current_user)) -> User:
    if user.role not in STAFF_ROLES:
        raise APIError(
            403,
            "FORBIDDEN",
            "Staff access only.",
            {"required_roles": [r.value for r in STAFF_ROLES], "your_role": user.role.value},
        )
    return user


def scope_query_to_customer(stmt: select, model, user: User) -> select:
    """Restrict a SELECT to the caller's own customer_id when they are a
    customer_user. Staff roles see everything. The model must expose a
    ``customer_id`` column for the restriction to apply.

    This is the single choke point for customer data isolation; routers should
    always run customer-visible queries through it rather than filtering ad hoc.
    """
    if user.role == UserRole.customer_user:
        if user.customer_id is None:
            # A customer_user with no customer_id can see nothing.
            raise APIError(403, "NO_CUSTOMER_SCOPE", "This account is not linked to a customer.")
        if hasattr(model, "customer_id"):
            stmt = stmt.where(model.customer_id == user.customer_id)
    return stmt
