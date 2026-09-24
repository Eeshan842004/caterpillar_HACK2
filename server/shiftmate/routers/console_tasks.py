"""Console task board and machines (technical spec §6.3; T32): list tasks with execution state, reassign or
cancel a task (supervisor), list site machines."""

import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from shiftmate.db import get_db
from shiftmate.errors import ShiftMateException
from shiftmate.models import ConsoleUser, Machine, TaskAssignment
from shiftmate.schemas.console import TaskReassignRequest
from shiftmate.security.console_auth import get_current_user, require_role
from shiftmate.services.tasks import reassign_task, task_with_exec
from shiftmate.services.ws_hub import notify

router = APIRouter(prefix="/console", tags=["console_tasks"])


@router.get("/tasks")
def list_tasks(
    machine_id: str | None = Query(None, pattern=r"^[A-Z]{2}-\d{2}$"),
    date: dt.date | None = None,
    db: Session = Depends(get_db),
    user: ConsoleUser = Depends(get_current_user),
):
    q = db.query(TaskAssignment).filter(TaskAssignment.site_id.in_(user.site_ids or []))
    if machine_id:
        q = q.filter(TaskAssignment.machine_id == machine_id)
    if date:
        q = q.filter(TaskAssignment.planned_date == date)
    rows = q.order_by(TaskAssignment.planned_date, TaskAssignment.machine_id, TaskAssignment.sequence).all()
    return {"items": [task_with_exec(t) for t in rows]}


@router.post("/tasks/{task_id}/reassign")
def reassign(
    task_id: str,
    req: TaskReassignRequest,
    db: Session = Depends(get_db),
    user: ConsoleUser = Depends(require_role("supervisor")),
):
    task = db.get(TaskAssignment, task_id)
    if task is None or task.site_id not in (user.site_ids or []):
        raise ShiftMateException(status_code=404, code="not_found", message="Task not found.")
    reassign_task(db, task, req.new_machine_id)
    notify(db, task.site_id, ["tasks"])
    db.commit()
    return task_with_exec(task)


@router.get("/machines")
def list_machines(
    site_id: str | None = None, db: Session = Depends(get_db), user: ConsoleUser = Depends(get_current_user)
):
    sites = [site_id] if site_id else list(user.site_ids or [])
    rows = db.query(Machine).filter(Machine.site_id.in_([s for s in sites if s in (user.site_ids or [])]))
    return {
        "items": [
            {
                "machine_id": m.machine_id,
                "short_id": m.short_id,
                "site_id": m.site_id,
                "profile_id": m.profile_id,
                "model_name": m.model_name,
                "detail_level": m.detail_level,
            }
            for m in rows.order_by(Machine.machine_id).all()
        ]
    }
