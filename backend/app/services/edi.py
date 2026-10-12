"""Mapping from internal event codes to EDI 214 status codes.

Used to auto-fill milestone.edi_214_code when a milestone is created without an
explicit code. Only the events that carry a standard 214 status are mapped.
"""
from app.models.milestone import EventCode

EVENT_TO_EDI_214: dict[EventCode, str] = {
    EventCode.PICKED_UP: "AF",                          # Carrier departed pickup
    EventCode.ARRIVED_AT_TERMINAL: "X3",                # Arrived at terminal
    EventCode.DEPARTED_TERMINAL: "AG",                  # Departed terminal
    EventCode.ARRIVED_AT_DESTINATION_TERMINAL: "X6",    # Arrived at destination
    EventCode.OUT_FOR_DELIVERY: "X1",                   # Out for delivery
    EventCode.DELIVERED: "D1",                           # Delivered
    EventCode.DELIVERY_ATTEMPTED: "SD",                  # Attempted delivery
    EventCode.APPOINTMENT_SET: "AB",                     # Delivery appointment
    EventCode.DELAYED: "SD",                             # Delayed / status change
    EventCode.CUSTOMS_HOLD: "X6",
}


def edi_214_for(event_code: EventCode) -> str | None:
    return EVENT_TO_EDI_214.get(event_code)
