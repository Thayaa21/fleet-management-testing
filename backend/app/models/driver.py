import enum
from datetime import date

from sqlalchemy import Date, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin


class DriverType(str, enum.Enum):
    city_pd = "city_pd"
    linehaul = "linehaul"


class DriverStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Driver(TimestampMixin, Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(50), default="")
    license_number: Mapped[str] = mapped_column(String(60), default="")
    license_province_state: Mapped[str] = mapped_column(String(60), default="")
    license_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    home_terminal_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    type: Mapped[DriverType] = mapped_column(Enum(DriverType, name="driver_type"), nullable=False)
    status: Mapped[DriverStatus] = mapped_column(
        Enum(DriverStatus, name="driver_status"), default=DriverStatus.active, nullable=False
    )
    hos_hours_remaining: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
