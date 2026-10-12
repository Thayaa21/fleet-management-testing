from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.driver import DriverStatus, DriverType


def _upper(v: str | None) -> str | None:
    return v.strip().upper() if isinstance(v, str) else v


class DriverBase(BaseModel):
    full_name: str
    phone: str = ""
    license_number: str = ""
    license_province_state: str = ""
    license_expiry: date | None = None
    home_terminal_id: int | None = None
    type: DriverType
    hos_hours_remaining: float = 0.0


class DriverCreate(DriverBase):
    employee_number: str

    @field_validator("employee_number")
    @classmethod
    def norm_emp(cls, v: str) -> str:
        return _upper(v)


class DriverUpdate(BaseModel):
    employee_number: str | None = None
    full_name: str | None = None
    phone: str | None = None
    license_number: str | None = None
    license_province_state: str | None = None
    license_expiry: date | None = None
    home_terminal_id: int | None = None
    type: DriverType | None = None
    status: DriverStatus | None = None
    hos_hours_remaining: float | None = None

    @field_validator("employee_number")
    @classmethod
    def norm_emp(cls, v: str | None) -> str | None:
        return _upper(v)


class DriverOut(DriverBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_number: str
    status: DriverStatus
