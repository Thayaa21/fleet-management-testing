from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import APIError
from app.models.milestone import Milestone
from app.schemas.milestone import MilestoneOut, VoidRequest
from app.services.auth import require_staff
from app.services.shipment_state import void_milestone

router = APIRouter(prefix="/milestones", tags=["milestones"], dependencies=[Depends(require_staff)])


@router.post("/{milestone_id}/void", response_model=MilestoneOut)
def void(milestone_id: int, body: VoidRequest, db: Session = Depends(get_db)):
    m = db.get(Milestone, milestone_id)
    if m is None:
        raise APIError(404, "NOT_FOUND", "Milestone not found.")
    if m.is_voided:
        raise APIError(409, "ALREADY_VOIDED", "Milestone is already voided.")
    void_milestone(db, m, body.reason)
    db.commit()
    db.refresh(m)
    return m
