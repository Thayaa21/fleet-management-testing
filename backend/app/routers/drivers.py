from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.driver import Driver, DriverStatus, DriverType
from app.models.location import Location
from app.schemas.common import Page
from app.schemas.driver import DriverCreate, DriverOut, DriverUpdate
from app.services.auth import require_staff
from app.services.crud import apply_search, clamp_page, ensure_unique, paginate
from app.services.refs import ensure_exists

router = APIRouter(prefix="/drivers", tags=["drivers"], dependencies=[Depends(require_staff)])


@router.get("", response_model=Page[DriverOut])
def list_drivers(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    status: DriverStatus | None = None,
    type: DriverType | None = None,
    home_terminal_id: int | None = None,
    include_inactive: bool = False,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(Driver)
    if status is not None:
        stmt = stmt.where(Driver.status == status)
    elif not include_inactive:
        stmt = stmt.where(Driver.status == DriverStatus.active)
    if type is not None:
        stmt = stmt.where(Driver.type == type)
    if home_terminal_id is not None:
        stmt = stmt.where(Driver.home_terminal_id == home_terminal_id)
    stmt = apply_search(stmt, q, [Driver.employee_number, Driver.full_name, Driver.license_number])
    stmt = stmt.order_by(Driver.full_name)

    items, total = paginate(db, stmt, p, ps)
    return Page[DriverOut](items=items, total=total, page=p, page_size=ps)


@router.post("", response_model=DriverOut, status_code=201)
def create_driver(body: DriverCreate, db: Session = Depends(get_db)):
    ensure_unique(db, Driver, Driver.employee_number, body.employee_number, "employee_number")
    ensure_exists(db, Location, body.home_terminal_id, "home_terminal_id")
    obj = Driver(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{driver_id}", response_model=DriverOut)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    obj = db.get(Driver, driver_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Driver not found.")
    return obj


@router.patch("/{driver_id}", response_model=DriverOut)
def update_driver(driver_id: int, body: DriverUpdate, db: Session = Depends(get_db)):
    obj = db.get(Driver, driver_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Driver not found.")
    data = body.model_dump(exclude_unset=True)
    if "employee_number" in data and data["employee_number"] != obj.employee_number:
        ensure_unique(db, Driver, Driver.employee_number, data["employee_number"], "employee_number", exclude_id=obj.id)
    if "home_terminal_id" in data:
        ensure_exists(db, Location, data["home_terminal_id"], "home_terminal_id")
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{driver_id}", response_model=DriverOut)
def deactivate_driver(driver_id: int, db: Session = Depends(get_db)):
    obj = db.get(Driver, driver_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Driver not found.")
    obj.status = DriverStatus.inactive
    db.commit()
    db.refresh(obj)
    return obj
