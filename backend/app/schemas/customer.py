from pydantic import BaseModel, ConfigDict, field_validator

from app.models.customer import CustomerStatus, CustomerType


def _upper(v: str | None) -> str | None:
    return v.strip().upper() if isinstance(v, str) else v


class CustomerBase(BaseModel):
    name: str
    type: CustomerType
    billing_address: str = ""
    billing_city: str = ""
    billing_province_state: str = ""
    billing_postal_zip: str = ""
    billing_country: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    payment_terms: str = ""
    credit_hold: bool = False
    notes: str = ""


class CustomerCreate(CustomerBase):
    account_number: str

    @field_validator("account_number")
    @classmethod
    def norm_account(cls, v: str) -> str:
        return _upper(v)


class CustomerUpdate(BaseModel):
    account_number: str | None = None
    name: str | None = None
    type: CustomerType | None = None
    billing_address: str | None = None
    billing_city: str | None = None
    billing_province_state: str | None = None
    billing_postal_zip: str | None = None
    billing_country: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    payment_terms: str | None = None
    credit_hold: bool | None = None
    status: CustomerStatus | None = None
    notes: str | None = None

    @field_validator("account_number")
    @classmethod
    def norm_account(cls, v: str | None) -> str | None:
        return _upper(v)


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_number: str
    status: CustomerStatus
