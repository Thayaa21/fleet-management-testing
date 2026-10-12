"""Generic list/search/pagination helpers shared by master-data routers."""
from typing import Sequence

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.schemas.common import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


def clamp_page(page: int | None, page_size: int | None) -> tuple[int, int]:
    p = max(1, page or 1)
    ps = page_size or DEFAULT_PAGE_SIZE
    ps = max(1, min(ps, MAX_PAGE_SIZE))
    return p, ps


def apply_search(stmt: Select, q: str | None, columns: Sequence[InstrumentedAttribute]) -> Select:
    """Case-insensitive LIKE across the given (string) columns."""
    if not q or not columns:
        return stmt
    like = f"%{q.strip().lower()}%"
    conditions = [func.lower(col).like(like) for col in columns]
    return stmt.where(or_(*conditions))


def paginate(db: Session, stmt: Select, page: int, page_size: int) -> tuple[list, int]:
    """Return (items, total) for the given SELECT statement."""
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.limit(page_size).offset((page - 1) * page_size)).all()
    return list(rows), int(total)


def ensure_unique(db: Session, model, column: InstrumentedAttribute, value, field: str, exclude_id: int | None = None):
    """Raise 409 CONFLICT if another row already has this value for the column."""
    from app.errors import APIError  # local import to avoid a cycle

    stmt = select(model).where(column == value)
    if exclude_id is not None:
        stmt = stmt.where(model.id != exclude_id)
    if db.scalar(stmt) is not None:
        raise APIError(
            409,
            "CONFLICT",
            f"{field} '{value}' already exists.",
            {"field": field, "value": value},
        )
