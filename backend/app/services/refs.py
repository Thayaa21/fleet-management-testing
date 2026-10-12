"""Foreign-key existence checks used by master-data services."""
from sqlalchemy.orm import Session

from app.errors import APIError


def ensure_exists(db: Session, model, id_: int | None, field: str) -> None:
    """Raise 422 INVALID_REFERENCE if a non-null id does not resolve to a row."""
    if id_ is None:
        return
    if db.get(model, id_) is None:
        raise APIError(
            422,
            "INVALID_REFERENCE",
            f"{field} does not reference an existing record.",
            {"field": field, "value": id_},
        )
