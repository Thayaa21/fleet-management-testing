import enum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin


class LocationType(str, enum.Enum):
    customer_site = "customer_site"
    terminal = "terminal"
    cross_dock = "cross_dock"
    customs_point = "customs_point"


class LocationStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Location(TimestampMixin, Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[LocationType] = mapped_column(Enum(LocationType, name="location_type"), nullable=False)

    address: Mapped[str] = mapped_column(String(255), default="")
    city: Mapped[str] = mapped_column(String(120), default="")
    province_state: Mapped[str] = mapped_column(String(60), default="")
    postal_zip: Mapped[str] = mapped_column(String(20), default="")
    country: Mapped[str] = mapped_column(String(2), default="")  # CA | US

    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    timezone: Mapped[str] = mapped_column(String(60), default="")
    dock_hours: Mapped[str] = mapped_column(String(120), default="")
    appointment_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    geofence_radius_m: Mapped[int] = mapped_column(Integer, default=300, nullable=False)

    status: Mapped[LocationStatus] = mapped_column(
        Enum(LocationStatus, name="location_status"), default=LocationStatus.active, nullable=False
    )
