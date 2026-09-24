from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from shiftmate.models import ChangeLog
from shiftmate.time_util import utc_now


def record_change(
    db: Session,
    change_type: str,
    scope_type: str,
    scope_id: str | None,
    payload: dict[str, Any],
) -> ChangeLog:
    change = ChangeLog(
        change_type=change_type,
        scope_type=scope_type,
        scope_id=scope_id,
        payload=payload,
        created_at=utc_now(),
    )
    db.add(change)
    db.flush()
    return change


def get_changes_for_device(
    db: Session,
    cursor: int,
    limit: int,
    machine_id: str,
    site_id: str,
    machine_class: str,
) -> tuple[list[dict[str, Any]], int, bool]:
    query = (
        db.query(ChangeLog)
        .filter(ChangeLog.seq > cursor)
        .filter(
            or_(
                ChangeLog.scope_type == "all",
                and_(ChangeLog.scope_type == "machine", ChangeLog.scope_id == machine_id),
                and_(ChangeLog.scope_type == "site", ChangeLog.scope_id == site_id),
                and_(ChangeLog.scope_type == "machine_class", ChangeLog.scope_id == machine_class),
            )
        )
        .order_by(ChangeLog.seq.asc())
        .limit(limit + 1)
    )

    rows = query.all()
    has_more = len(rows) > limit
    selected = rows[:limit]

    changes = [
        {
            "seq": row.seq,
            "change_type": row.change_type,
            "scope_type": row.scope_type,
            "scope_id": row.scope_id,
            "created_at": row.created_at.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "payload": row.payload,
        }
        for row in selected
    ]

    next_cursor = selected[-1].seq if selected else cursor
    return changes, next_cursor, has_more
