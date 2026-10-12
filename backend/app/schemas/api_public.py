from datetime import date

from pydantic import BaseModel


class PublicShipmentCreate(BaseModel):
    shipper_city: str
    shipper_province_state: str
    shipper_postal_zip: str
    shipper_country: str
    consignee_city: str
    consignee_province_state: str
    consignee_postal_zip: str
    consignee_country: str
    pickup_date: date
    total_weight_lbs: float
    freight_class: str = ""
    bol_number: str = ""
    po_numbers: list[str] = []
    customer_reference: str = ""


class PublicPickupCreate(BaseModel):
    location_city: str
    location_province_state: str
    location_postal_zip: str
    location_country: str
    requested_date: date
    expected_pieces: int = 0
    expected_weight_lbs: float = 0.0
    notes: str = ""
