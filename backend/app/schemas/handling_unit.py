from pydantic import BaseModel, ConfigDict

from app.models.shipment import HandlingUnitType


class HandlingUnitBase(BaseModel):
    type: HandlingUnitType = HandlingUnitType.skid
    quantity: int = 1
    length_in: float | None = None
    width_in: float | None = None
    height_in: float | None = None
    weight_lbs: float | None = None
    stackable: bool = False
    description: str = ""
    label_barcode: str | None = None


class HandlingUnitCreate(HandlingUnitBase):
    pass


class HandlingUnitOut(HandlingUnitBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipment_id: int
