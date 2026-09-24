"""Console follow-ups (technical spec §6.3, C2): list, detail, assign, resolve, comment."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from shiftmate.db import get_db
from shiftmate.errors import ShiftMateException
from shiftmate.models import (
    ConsoleUser,
    FollowUp,
    FollowUpComment,
    FollowUpContribution,
    LedgerEntry,
    Operator,
)
from shiftmate.schemas.console import (
    AssignRequest,
    Comment,
    CommentRequest,
    Contribution,
    FollowUpDetail,
    FollowUpList,
    FollowUpSummary,
    ResolveRequest,
)
from shiftmate.security.console_auth import get_current_user
from shiftmate.services.changes import record_change
from shiftmate.services.console_actions import decode_cursor, encode_cursor, server_entry
from shiftmate.time_util import iso_ms, utc_now

router = APIRouter(prefix="/console/follow-ups", tags=["console_followups"])

# Role visibility (§5.2); trainers read safety incidents but cannot act on them (§9.2)
ROLE_CATEGORIES = {
    "supervisor": ["site_delay", "machine_check", "assignment_request", "supervisor_notification", "sync_conflict",
                   "near_miss_cluster", "overspeed_zone", "usage_review", "sos", "chain_integrity", "alert_review"],
    "safety": ["safety_incident", "near_miss_cluster", "alert_review", "sos", "chain_integrity"],
    "trainer": ["help_request", "safety_incident"],
    "mechanic": ["machine_check"],
}
READ_ONLY = {("trainer", "safety_incident")}


def _summary(fu: FollowUp) -> FollowUpSummary:
    return FollowUpSummary(
        follow_up_id=fu.follow_up_id, site_id=fu.site_id, category=fu.category, title=fu.title, summary=fu.summary,
        priority=fu.priority, status=fu.status, assigned_to=fu.assigned_to, machine_id=fu.machine_id,
        zone_id=fu.zone_id, reason_code=fu.reason_code, metrics=fu.metrics or {},
        first_seen_at=iso_ms(fu.first_seen_at), last_seen_at=iso_ms(fu.last_seen_at),
    )


def _load(db: Session, user: ConsoleUser, follow_up_id: str, *, write: bool) -> FollowUp:
    fu = db.get(FollowUp, follow_up_id)
    if fu is None or fu.site_id not in (user.site_ids or []) or fu.category not in ROLE_CATEGORIES.get(user.role, []):
        raise ShiftMateException(status_code=404, code="not_found", message="Follow-up not found.")
    if write and (user.role, fu.category) in READ_ONLY:
        raise ShiftMateException(status_code=403, code="forbidden", message="Your role can read but not act on this item.")
    return fu


def _detail(db: Session, fu: FollowUp) -> FollowUpDetail:
    contributions = []
    for c in db.query(FollowUpContribution).filter(FollowUpContribution.follow_up_id == fu.follow_up_id).all():
        root = db.get(LedgerEntry, c.entry_id)
        reason_entry = None
        if root is not None and root.payload.get("related_entry_ids"):
            reason_entry = db.get(LedgerEntry, root.payload["related_entry_ids"][0])
        op = db.get(Operator, root.operator_id) if root is not None and root.operator_id else None
        contributions.append(Contribution(
            entry_id=c.entry_id, minutes=c.minutes, active=c.active, machine_id=root.machine_id if root else None,
            operator_display=op.display_name if op else None, observed_at=iso_ms(root.observed_at) if root else None,
            original_text=reason_entry.original_text if reason_entry else None,
        ))
    comments = [Comment(comment_id=c.comment_id, user_id=c.user_id, text=c.text, created_at=iso_ms(c.created_at))
                for c in db.query(FollowUpComment).filter(FollowUpComment.follow_up_id == fu.follow_up_id)
                .order_by(FollowUpComment.created_at).all()]
    related = {}
    if fu.related_id:
        entry = db.get(LedgerEntry, fu.related_id)
        related = {"related_id": fu.related_id, "entry": {"kind": entry.kind, "subtype": entry.subtype,
                                                          "payload": entry.payload} if entry else None}
    return FollowUpDetail(**_summary(fu).model_dump(), contributions=contributions, comments=comments, related=related,
                          resolved_at=iso_ms(fu.resolved_at) if fu.resolved_at else None,
                          resolution_note=fu.resolution_note)


@router.get("", response_model=FollowUpList)
def list_followups(
    status: str = Query("open", pattern="^(open|resolved|all)$"),
    category: str | None = None,
    site_id: str | None = None,
    cursor: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: ConsoleUser = Depends(get_current_user),
):
    allowed = ROLE_CATEGORIES.get(user.role, [])
    q = db.query(FollowUp).filter(FollowUp.category.in_(allowed), FollowUp.site_id.in_(user.site_ids or []))
    if status == "open":
        q = q.filter(FollowUp.status != "resolved")
    elif status == "resolved":
        q = q.filter(FollowUp.status == "resolved")
    if category:
        q = q.filter(FollowUp.category == category)
    if site_id:
        q = q.filter(FollowUp.site_id == site_id)
    if cursor:
        prio, first_seen, fid = decode_cursor(cursor)
        first_dt = datetime.fromisoformat(first_seen)
        q = q.filter(or_(FollowUp.priority > prio,
                         and_(FollowUp.priority == prio, FollowUp.first_seen_at > first_dt),
                         and_(FollowUp.priority == prio, FollowUp.first_seen_at == first_dt, FollowUp.follow_up_id > fid)))
    rows = q.order_by(FollowUp.priority.asc(), FollowUp.first_seen_at.asc(), FollowUp.follow_up_id.asc()).limit(limit + 1).all()
    page = rows[:limit]
    nxt = encode_cursor([page[-1].priority, page[-1].first_seen_at.isoformat(), page[-1].follow_up_id]) \
        if len(rows) > limit else None
    return FollowUpList(items=[_summary(r) for r in page], next_cursor=nxt)


@router.get("/{follow_up_id}", response_model=FollowUpDetail)
def get_followup(follow_up_id: str, db: Session = Depends(get_db), user: ConsoleUser = Depends(get_current_user)):
    return _detail(db, _load(db, user, follow_up_id, write=False))


@router.post("/{follow_up_id}/assign", response_model=FollowUpDetail)
def assign_followup(follow_up_id: str, req: AssignRequest, db: Session = Depends(get_db),
                    user: ConsoleUser = Depends(get_current_user)):
    fu = _load(db, user, follow_up_id, write=True)
    if fu.status == "resolved":
        raise ShiftMateException(status_code=409, code="invalid_state", message="Follow-up is already resolved.")
    fu.assigned_to = req.user_id
    fu.status = "assigned" if req.user_id else "open"
    fu.updated_at = utc_now()
    db.commit()
    return _detail(db, fu)


@router.post("/{follow_up_id}/resolve", response_model=FollowUpDetail)
def resolve_followup(follow_up_id: str, req: ResolveRequest, db: Session = Depends(get_db),
                     user: ConsoleUser = Depends(get_current_user)):
    fu = _load(db, user, follow_up_id, write=True)
    if fu.status == "resolved":
        raise ShiftMateException(status_code=409, code="invalid_state", message="Follow-up is already resolved.")
    now = utc_now()
    fu.status, fu.resolved_at, fu.resolved_by, fu.resolution_note, fu.updated_at = "resolved", now, user.user_id, req.note, now

    contributions = db.query(FollowUpContribution).filter(FollowUpContribution.follow_up_id == fu.follow_up_id).all()
    machines = {fu.machine_id} if fu.machine_id else set()
    for c in contributions:
        root = db.get(LedgerEntry, c.entry_id)
        if root:
            machines.add(root.machine_id)
    for machine_id in sorted(machines):
        record_change(db, "followup.resolved", "machine", machine_id,
                      {"follow_up_id": fu.follow_up_id, "category": fu.category,
                       "related_entry_ids": [c.entry_id for c in contributions], "note": req.note or None})

    if fu.category == "sync_conflict" and fu.related_id:
        entry = db.get(LedgerEntry, fu.related_id)
        if entry:
            entry.review_status = "ok"
            record_change(db, "conflict.resolved", "machine", entry.machine_id,
                          {"entry_id": entry.entry_id, "resolution": "accepted", "note": req.note or None})
    if fu.category == "alert_review" and fu.related_id:
        # Resolving an alert review marks the alert REVIEWED (§5.3.2 alert/reviewed, server-authored)
        raised = db.query(LedgerEntry).filter(LedgerEntry.kind == "alert", LedgerEntry.subtype == "raised").all()
        source = next((r for r in raised if r.payload.get("alert_id") == fu.related_id), None)
        if source is not None:
            server_entry(db, user, kind="alert", subtype="reviewed", machine_id=source.machine_id, audience="site",
                         payload={"alert_id": fu.related_id, "alert_type": source.payload["alert_type"],
                                  "follow_up_id": fu.follow_up_id, "note": req.note or None})
    db.commit()
    return _detail(db, fu)


@router.post("/{follow_up_id}/comments", response_model=Comment)
def comment_followup(follow_up_id: str, req: CommentRequest, db: Session = Depends(get_db),
                     user: ConsoleUser = Depends(get_current_user)):
    fu = _load(db, user, follow_up_id, write=False)
    c = FollowUpComment(follow_up_id=fu.follow_up_id, user_id=user.user_id, text=req.text, created_at=utc_now())
    db.add(c)
    db.commit()
    return Comment(comment_id=c.comment_id, user_id=c.user_id, text=c.text, created_at=iso_ms(c.created_at))
