import enum

from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin


class CustomerType(str, enum.Enum):
    shipper = "shipper"
    consignee = "consignee"
    both = "both"
    third_party_payer = "third_party_payer"


class CustomerStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[CustomerType] = mapped_column(Enum(CustomerType, name="customer_type"), nullable=False)

    billing_address: Mapped[str] = mapped_column(String(255), default="")
    billing_city: Mapped[str] = mapped_column(String(120), default="")
    billing_province_state: Mapped[str] = mapped_column(String(60), default="")
    billing_postal_zip: Mapped[str] = mapped_column(String(20), default="")
    billing_country: Mapped[str] = mapped_column(String(2), default="")

    contact_name: Mapped[str] = mapped_column(String(255), default="")
    contact_email: Mapped[str] = mapped_column(String(255), default="")
    contact_phone: Mapped[str] = mapped_column(String(50), default="")

    payment_terms: Mapped[str] = mapped_column(String(50), default="")
    credit_hold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus, name="customer_status"), default=CustomerStatus.active, nullable=False
    )
    notes: Mapped[str] = mapped_column(Text, default="")
