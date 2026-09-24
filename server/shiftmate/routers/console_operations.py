"""Console reassignment decisions, handovers and help answers (technical spec §6.3, C2/C5)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from shiftmate.db import get_db
from shiftmate.errors import ThroughlineException
from shiftmate.models import (
    ConsoleUser,
    FollowUp,
    Handover,
    HandoverItem,
    HelpRequest,
    Machine,
    ReassignmentRequest,
    TaskAssignment,
)
from shiftmate.schemas.console import HandoverItemResolveRequest, HelpAnswerRequest, ReassignDecisionRequest
from shiftmate.security.console_auth import get_current_user, require_role
from shiftmate.services.changes import record_change
from shiftmate.time_util import iso_ms, utc_now

router = APIRouter(prefix="/console", tags=["console_operations"])


def _task_wire(t: TaskAssignment) -> dict:
    return {"task_id": t.task_id, "site_id": t.site_id, "machine_id": t.machine_id, "task_type": t.task_type,
            "zone_id": t.zone_id, "location_text": t.location_text, "quantity": t.quantity, "unit": t.unit,
            "material": t.material, "priority": t.priority, "completion_criterion": t.completion_criterion,
            "planner_minutes": t.planner_minutes, "planned_date": t.planned_date.isoformat(),
            "planned_start_at": iso_ms(t.planned_start_at) if t.planned_start_at else None,
            "planned_start_window_min": t.planned_start_window_min, "sequence": t.sequence, "source": t.source,
            "revision": t.revision, "status": t.status}


def _resolve_group(db: Session, group_key: str, user: ConsoleUser, note: str | None) -> None:
    fu = db.query(FollowUp).filter(FollowUp.group_key == group_key, FollowUp.status != "resolved").first()
    if fu:
        fu.status, fu.resolved_at, fu.resolved_by, fu.resolution_note = "resolved", utc_now(), user.user_id, note


@router.post("/reassignment-requests/{request_id}/decide")
def decide_reassignment(request_id: str, req: ReassignDecisionRequest, db: Session = Depends(get_db),
                        user: ConsoleUser = Depends(require_role("supervisor"))):
    rr = db.get(ReassignmentRequest, request_id)
    task = db.get(TaskAssignment, rr.task_id) if rr else None
    if rr is None or task is None or task.site_id not in (user.site_ids or []):
        raise ThroughlineException(status_code=404, code="not_found", message="Request not found.")
    if rr.status != "pending":
        raise ThroughlineException(status_code=409, code="invalid_state", message="Request is already decided.")
    old_machine = task.machine_id
    if req.decision == "accept":
        if req.new_machine_id:
            target = db.get(Machine, req.new_machine_id)
            if target is None or target.site_id != task.site_id:
                raise ThroughlineException(status_code=422, code="validation_error", message="Unknown machine for this site.")
            task.machine_id, task.source = req.new_machine_id, "reassignment"
            record_change(db, "task_assignment.removed", "machine", old_machine,
                          {"task_id": task.task_id, "reason": "reassigned", "new_machine_id": req.new_machine_id})
            task.revision += 1
            record_change(db, "task_assignment.upsert", "machine", req.new_machine_id, _task_wire(task))
        else:
            task.status = "cancelled"
            task.revision += 1
            record_change(db, "task_assignment.removed", "machine", old_machine,
                          {"task_id": task.task_id, "reason": "cancelled", "new_machine_id": None})
        rr.status = "accepted"
    else:
        rr.status = "rejected"
    rr.decided_by, rr.decided_at, rr.new_machine_id, rr.decision_note = user.user_id, utc_now(), req.new_machine_id, req.note
    task.updated_at = utc_now()
    record_change(db, "reassignment.decided", "machine", old_machine,
                  {"request_id": rr.request_id, "task_id": task.task_id,
                   "decision": "accepted" if rr.status == "accepted" else "rejected",
                   "new_machine_id": req.new_machine_id, "note": req.note})
    _resolve_group(db, f"reassign:{request_id}", user, req.note)
    db.commit()
    return {"request": {"request_id": rr.request_id, "status": rr.status}, "task": _task_wire(task)}


@router.get("/handovers")
def list_handovers(machine_id: str | None = None, status: str = Query("open", pattern="^(open|all)$"),
                   db: Session = Depends(get_db), user: ConsoleUser = Depends(get_current_user)):
    site_machines = {m.machine_id for m in db.query(Machine).filter(Machine.site_id.in_(user.site_ids or [])).all()}
    q = db.query(Handover).filter(Handover.machine_id.in_(site_machines))
    if machine_id:
        q = q.filter(Handover.machine_id == machine_id)
    out = []
    for ho in q.order_by(Handover.created_at.desc()).all():
        items = db.query(HandoverItem).filter(HandoverItem.handover_id == ho.handover_id)
        if status == "open":
            items = items.filter(HandoverItem.status == "open")
        rows = items.all()
        if not rows and status == "open":
            continue
        out.append({"handover": {"handover_id": ho.handover_id, "machine_id": ho.machine_id,
                                 "from_operator_id": ho.from_operator_id, "created_at": iso_ms(ho.created_at),
                                 "voice_note_upload_id": ho.voice_note_upload_id, "wording_method": ho.wording_method},
                    "items": [{"item_id": i.item_id, "item_type": i.item_type, "text": i.text, "audiences": i.audiences,
                               "status": i.status, "task_id": i.task_id, "incident_id": i.incident_id,
                               "acknowledged_by": i.acknowledged_by,
                               "acknowledged_at": iso_ms(i.acknowledged_at) if i.acknowledged_at else None,
                               "resolved_by": i.resolved_by,
                               "resolved_at": iso_ms(i.resolved_at) if i.resolved_at else None} for i in rows]})
    return {"items": out}


@router.post("/handover-items/{item_id}/resolve")
def resolve_handover_item(item_id: str, req: HandoverItemResolveRequest, db: Session = Depends(get_db),
                          user: ConsoleUser = Depends(require_role("supervisor", "mechanic"))):
    item = db.get(HandoverItem, item_id)
    handover = db.get(Handover, item.handover_id) if item else None
    machine = db.get(Machine, handover.machine_id) if handover else None
    if item is None or machine is None or machine.site_id not in (user.site_ids or []):
        raise ThroughlineException(status_code=404, code="not_found", message="Handover item not found.")
    if item.status != "open":
        raise ThroughlineException(status_code=409, code="invalid_state", message="Item is not open.")
    item.status, item.resolved_by, item.resolved_at, item.resolution_note = "resolved", user.user_id, utc_now(), req.note
    record_change(db, "handover_item.resolved", "machine", handover.machine_id,
                  {"item_id": item.item_id, "resolved_by_role": user.role, "resolved_at": iso_ms(item.resolved_at),
                   "note": req.note or None})
    db.commit()
    return {"item_id": item.item_id, "status": item.status, "resolved_by": item.resolved_by,
            "resolved_at": iso_ms(item.resolved_at)}


@router.post("/help-requests/{request_id}/answer")
def answer_help(request_id: str, req: HelpAnswerRequest, db: Session = Depends(get_db),
                user: ConsoleUser = Depends(require_role("trainer"))):
    hr = db.get(HelpRequest, request_id)
    machine = db.get(Machine, hr.machine_id) if hr else None
    if hr is None or machine is None or machine.site_id not in (user.site_ids or []):
        raise ThroughlineException(status_code=404, code="not_found", message="Help request not found.")
    if hr.status == "answered":
        raise ThroughlineException(status_code=409, code="invalid_state", message="Already answered.")
    hr.status, hr.answered_by, hr.answer_text, hr.answered_at = "answered", user.user_id, req.answer_text, utc_now()
    record_change(db, "help_request.answered", "machine", hr.machine_id,
                  {"request_id": hr.request_id, "operator_id": hr.operator_id, "content_id": hr.content_id,
                   "answer_text": hr.answer_text, "answered_at": iso_ms(hr.answered_at)})
    _resolve_group(db, f"help:{request_id}", user, "Answered")
    db.commit()
    return {"request": {"request_id": hr.request_id, "status": hr.status}}
