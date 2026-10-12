"""SQLAlchemy models. Import models here so Alembic's autogenerate and
metadata.create_all see them."""
from app.models.customer import Customer, CustomerStatus, CustomerType
from app.models.driver import Driver, DriverStatus, DriverType
from app.models.equipment import (
    AttachedToType,
    DeviceStatus,
    TelematicsDevice,
    TelematicsProvider,
    Tractor,
    TractorStatus,
    Trailer,
    TrailerStatus,
    TrailerType,
)
from app.models.location import Location, LocationStatus, LocationType
from app.models.audit import ActorType, AuditAction, AuditLog
from app.models.telematics import GpsPing, IngestErrorCode, TelematicsIngestLog
from app.models.billing import (
    Accessorial,
    Document,
    DocumentType,
    Exception_,
    ExceptionSeverity,
    ExceptionSource,
    ExceptionStatus,
    ExceptionType,
    FreightBill,
    FreightBillStatus,
    FuelSurcharge,
    RateTable,
    ShipmentAccessorial,
)
from app.models.api import (
    ApiClient,
    ApiClientStatus,
    ApiErrorCode,
    ApiKey,
    ApiRequestLog,
    IdempotencyKey,
    IpAllowlist,
    WebhookDelivery,
    WebhookError,
    WebhookSubscription,
    WebhookSubStatus,
)
from app.models.operations import (
    Manifest,
    ManifestItem,
    ManifestStatus,
    PickupChannel,
    PickupRequest,
    PickupStatus,
    TrailerPosition,
    Trip,
    TripStatus,
    TripTrailer,
    TripType,
)
from app.models.milestone import EventCode, Milestone, MilestoneSource
from app.models.shipment import (
    HandlingUnit,
    HandlingUnitType,
    ServiceLevel,
    Shipment,
    ShipmentSource,
    ShipmentStatus,
)
from app.models.user import User, UserRole

__all__ = [
    "User", "UserRole",
    "Customer", "CustomerType", "CustomerStatus",
    "Location", "LocationType", "LocationStatus",
    "TelematicsDevice", "TelematicsProvider", "AttachedToType", "DeviceStatus",
    "Tractor", "TractorStatus",
    "Trailer", "TrailerType", "TrailerStatus",
    "Driver", "DriverType", "DriverStatus",
    "Shipment", "ShipmentStatus", "ServiceLevel", "ShipmentSource",
    "HandlingUnit", "HandlingUnitType",
    "Milestone", "EventCode", "MilestoneSource",
    "AuditLog", "AuditAction", "ActorType",
    "PickupRequest", "PickupStatus", "PickupChannel",
    "Trip", "TripType", "TripStatus", "TripTrailer", "TrailerPosition",
    "Manifest", "ManifestStatus", "ManifestItem",
    "GpsPing", "TelematicsIngestLog", "IngestErrorCode",
    "ApiClient", "ApiClientStatus", "ApiKey", "IpAllowlist", "ApiRequestLog",
    "ApiErrorCode", "WebhookSubscription", "WebhookSubStatus", "WebhookDelivery",
    "WebhookError", "IdempotencyKey",
    "Document", "DocumentType",
    "Exception_", "ExceptionType", "ExceptionSeverity", "ExceptionStatus", "ExceptionSource",
    "RateTable", "FuelSurcharge", "Accessorial", "ShipmentAccessorial",
    "FreightBill", "FreightBillStatus",
]
