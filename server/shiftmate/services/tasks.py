"""Task assignment changes shared by the reassignment decision and direct reassignment (technical spec §6.3, T32)."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from shiftmate.errors import ShiftMateException
from shiftmate.models import Machine, TaskAssignment
from shiftmate.services.changes import record_change
from shiftmate.time_util import iso_ms, utc_now


def task_wire(t: TaskAssignment) -> dict[str, Any]:
    """`TaskAssignment` wire shape (§6.2) as sent on `task_assignment.upsert`."""
    return {
        "task_id": t.task_id,
        "site_id": t.site_id,
        "machine_id": t.machine_id,
        "task_type": t.task_type,
        "zone_id": t.zone_id,
        "location_text": t.location_text,
        "quantity": t.quantity,
        "unit": t.unit,
        "material": t.material,
        "priority": t.priority,
        "completion_criterion": t.completion_criterion,
        "planner_minutes": t.planner_minutes,
        "planned_date": t.planned_date.isoformat(),
        "planned_start_at": iso_ms(t.planned_start_at) if t.planned_start_at else None,
        "planned_start_window_min": t.planned_start_window_min,
        "sequence": t.sequence,
        "source": t.source,
        "revision": t.revision,
        "status": t.status,
    }


def task_with_exec(t: TaskAssignment) -> dict[str, Any]:
    """Wire shape + the server's execution projection (console task list)."""
    return {
        **task_wire(t),
        "exec_state": t.exec_state,
        "exec_updated_at": iso_ms(t.exec_updated_at) if t.exec_updated_at else None,
        "actual_start": iso_ms(t.actual_start) if t.actual_start else None,
        "actual_end": iso_ms(t.actual_end) if t.actual_end else None,
        "active_min": t.active_min,
        "waiting_min": t.waiting_min,
        "output_qty": t.output_qty,
    }


def reassign_task(db: Session, task: TaskAssignment, new_machine_id: str | None) -> str | None:
    """Moves `task` to `new_machine_id` (same site) or cancels it (None); bumps the revision and records
    `task_assignment.removed` (old machine) + `task_assignment.upsert` (new machine). Returns the old machine."""
    if task.status == "cancelled":
        raise ShiftMateException(status_code=409, code="invalid_state", message="Task is cancelled.")
    old_machine = task.machine_id
    if new_machine_id:
        target = db.get(Machine, new_machine_id)
        if target is None or target.site_id != task.site_id:
            raise ShiftMateException(
                status_code=422, code="validation_error", message="Unknown machine for this site."
            )
        if new_machine_id == old_machine:
            raise ShiftMateException(
                status_code=422, code="validation_error", message="Task is already on that machine."
            )
        task.machine_id, task.source = new_machine_id, "reassignment"
        task.revision += 1
        if old_machine:
            record_change(
                db,
                "task_assignment.removed",
                "machine",
                old_machine,
                {"task_id": task.task_id, "reason": "reassigned", "new_machine_id": new_machine_id},
            )
        record_change(db, "task_assignment.upsert", "machine", new_machine_id, task_wire(task))
    else:
        task.status = "cancelled"
        task.revision += 1
        if old_machine:
            record_change(
                db,
                "task_assignment.removed",
                "machine",
                old_machine,
                {"task_id": task.task_id, "reason": "cancelled", "new_machine_id": None},
            )
    task.updated_at = utc_now()
    return old_machine
