from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.customer import Customer, CustomerStatus, CustomerType
from app.schemas.common import Page
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate
from app.services.auth import require_staff
from app.services.crud import apply_search, clamp_page, ensure_unique, paginate

router = APIRouter(prefix="/customers", tags=["customers"], dependencies=[Depends(require_staff)])


@router.get("", response_model=Page[CustomerOut])
def list_customers(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = None,
    status: CustomerStatus | None = None,
    type: CustomerType | None = None,
    credit_hold: bool | None = None,
    include_inactive: bool = False,
):
    p, ps = clamp_page(page, page_size)
    stmt = select(Customer)
    if status is not None:
        stmt = stmt.where(Customer.status == status)
    elif not include_inactive:
        stmt = stmt.where(Customer.status == CustomerStatus.active)
    if type is not None:
        stmt = stmt.where(Customer.type == type)
    if credit_hold is not None:
        stmt = stmt.where(Customer.credit_hold == credit_hold)
    stmt = apply_search(stmt, q, [Customer.account_number, Customer.name, Customer.contact_name])
    stmt = stmt.order_by(Customer.name)

    items, total = paginate(db, stmt, p, ps)
    return Page[CustomerOut](items=items, total=total, page=p, page_size=ps)


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(body: CustomerCreate, db: Session = Depends(get_db)):
    ensure_unique(db, Customer, Customer.account_number, body.account_number, "account_number")
    obj = Customer(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    obj = db.get(Customer, customer_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Customer not found.")
    return obj


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, body: CustomerUpdate, db: Session = Depends(get_db)):
    obj = db.get(Customer, customer_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Customer not found.")
    data = body.model_dump(exclude_unset=True)
    if "account_number" in data and data["account_number"] != obj.account_number:
        ensure_unique(db, Customer, Customer.account_number, data["account_number"], "account_number", exclude_id=obj.id)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{customer_id}", response_model=CustomerOut)
def deactivate_customer(customer_id: int, db: Session = Depends(get_db)):
    obj = db.get(Customer, customer_id)
    if obj is None:
        raise APIError(404, "NOT_FOUND", "Customer not found.")
    obj.status = CustomerStatus.inactive  # soft delete
    db.commit()
    db.refresh(obj)
    return obj
