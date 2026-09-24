"""Console SOS (technical spec §6.3 GET /console/sos, POST /console/sos/{id}/acknowledge, C7; T41 / S5).
Supervisor and safety, site-scoped."""

from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy.orm import Session

from shiftmate.db import get_db
from shiftmate.errors import ShiftMateException
from shiftmate.models import ConsoleUser, FollowUp, Machine, SosEvent
from shiftmate.schemas.common import StrictBaseModel
from shiftmate.security.console_auth import require_role
from shiftmate.services.sos import is_active, sos_wire
from shiftmate.services.ws_hub import notify
from shiftmate.time_util import utc_now

router = APIRouter(prefix="/console/sos", tags=["console_sos"])
responders = require_role("supervisor", "safety")


class AcknowledgeRequest(StrictBaseModel):
    response_note: str = Field(default="", max_length=500)


def _site_events(db: Session, user: ConsoleUser):
    return (
        db.query(SosEvent)
        .join(Machine, Machine.machine_id == SosEvent.machine_id)
        .filter(Machine.site_id.in_(user.site_ids or []))
    )


@router.get("")
def list_sos(
    status: str = Query("active", pattern="^(active|all)$"),
    db: Session = Depends(get_db),
    user: ConsoleUser = Depends(responders),
):
    events = _site_events(db, user).order_by(SosEvent.received_at.desc()).all()
    if status == "active":
        events = [e for e in events if is_active(db, e)]
    return {"items": [sos_wire(db, e) for e in events]}


@router.post("/{sos_id}/acknowledge")
def acknowledge(
    sos_id: str,
    req: AcknowledgeRequest,
    db: Session = Depends(get_db),
    user: ConsoleUser = Depends(responders),
):
    ev = _site_events(db, user).filter(SosEvent.sos_id == sos_id).first()
    if ev is None or ev.event_type != "sos":
        raise ShiftMateException(status_code=404, code="not_found", message="SOS not found.")
    if ev.acknowledged_at is not None:
        raise ShiftMateException(
            status_code=409, code="invalid_state", message="SOS is already acknowledged."
        )
    now = utc_now()
    ev.acknowledged_by, ev.acknowledged_at, ev.response_note = user.user_id, now, req.response_note or None
    fu = (
        db.query(FollowUp)
        .filter(FollowUp.group_key == f"sos:{sos_id}", FollowUp.status != "resolved")
        .first()
    )
    if fu is not None:
        fu.status, fu.resolved_at, fu.resolved_by, fu.updated_at = "resolved", now, user.user_id, now
        fu.resolution_note = req.response_note or "Acknowledged"
    machine = db.get(Machine, ev.machine_id)
    notify(db, machine.site_id, ["sos", "follow-ups"])
    db.commit()
    return sos_wire(db, ev)
