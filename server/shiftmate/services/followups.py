"""Follow-up aggregation (technical spec §8.21).

Follow-ups are grouped by `group_key`; at most one open row exists per key (partial unique index). Site-delay
follow-ups aggregate contributions from `inference/finding` entries; a correction moves the contribution of the
root finding between groups, so the console reflects the operator's corrected explanation (explain once).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from shiftmate.models import FollowUp, FollowUpContribution
from shiftmate.time_util import utc_now

REASON_LABELS = {
    "waiting_truck": "Truck wait",
    "waiting_loader": "Loader wait",
    "shovel_queue": "Shovel queue",
    "crusher_queue": "Crusher queue",
    "access_blocked": "Access blocked",
    "instructed_hold": "Instructed hold",
    "break": "Break",
    "other": "Other wait",
}


def open_group(
    db: Session,
    *,
    site_id: str,
    category: str,
    group_key: str,
    title: str,
    summary: str,
    priority: int,
    at: datetime,
    machine_id: str | None = None,
    zone_id: str | None = None,
    reason_code: str | None = None,
    related_id: str | None = None,
    metrics: dict[str, Any] | None = None,
) -> FollowUp:
    """Returns the open follow-up for `group_key`, creating it if needed (locks the row on PostgreSQL)."""
    query = db.query(FollowUp).filter(FollowUp.group_key == group_key, FollowUp.status != "resolved")
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        query = query.with_for_update()
    fu = query.first()
    now = utc_now()
    if fu is None:
        fu = FollowUp(
            site_id=site_id,
            category=category,
            group_key=group_key,
            title=title,
            summary=summary,
            priority=priority,
            status="open",
            machine_id=machine_id,
            zone_id=zone_id,
            reason_code=reason_code,
            related_id=related_id,
            metrics=metrics or {},
            first_seen_at=at,
            last_seen_at=at,
            created_at=now,
            updated_at=now,
        )
        db.add(fu)
        db.flush()
    else:
        fu.last_seen_at = max(fu.last_seen_at, at)
        fu.updated_at = now
        if metrics is not None:
            fu.metrics = metrics
    return fu


def _recompute_site_delay(db: Session, fu: FollowUp, zone_name: str | None) -> None:
    rows = (
        db.query(FollowUpContribution)
        .filter(FollowUpContribution.follow_up_id == fu.follow_up_id, FollowUpContribution.active.is_(True))
        .all()
    )
    count = len(rows)
    total = round(sum(r.minutes for r in rows), 1)
    fu.metrics = {"count": count, "total_minutes": total}
    label = REASON_LABELS.get(fu.reason_code or "", fu.reason_code or "Wait")
    where = zone_name or "site"
    fu.title = f"{label} at {where} — {count} reports, {total:g} min total today"
    fu.summary = f"{count} reported {label.lower()} event(s) at {where}, {total:g} min in total."
    fu.priority = 2 if total >= 30 else 3
    fu.updated_at = utc_now()
    if count == 0 and fu.status != "resolved":
        fu.status = "resolved"
        fu.resolved_at = utc_now()
        fu.resolution_note = "All reports corrected"


def set_site_delay_contribution(
    db: Session,
    *,
    root_entry_id: str,
    finding: dict[str, Any] | None,
    at: datetime,
    zone_name: str | None,
) -> None:
    """Upserts the contribution of one finding (by root entry id). `finding=None` retracts it."""
    contribution = db.get(FollowUpContribution, root_entry_id)
    old_fu = db.get(FollowUp, contribution.follow_up_id) if contribution else None

    if (
        finding is None
        or finding.get("owner") != "site"
        or finding.get("pattern_code") != "idle_reported_wait"
    ):
        if contribution is not None:
            contribution.active = False
            contribution.updated_at = utc_now()
            db.flush()
            if old_fu is not None:
                _recompute_site_delay(db, old_fu, zone_name)
        return

    group_key = (
        f"site_delay:{finding['site_id']}:{finding.get('zone_id') or 'none'}:"
        f"{finding.get('reason_code')}:{finding['local_date']}"
    )
    fu = open_group(
        db,
        site_id=finding["site_id"],
        category="site_delay",
        group_key=group_key,
        title="Site delay",
        summary="Site delay",
        priority=3,
        at=at,
        machine_id=finding.get("machine_id"),
        zone_id=finding.get("zone_id"),
        reason_code=finding.get("reason_code"),
    )
    if contribution is None:
        contribution = FollowUpContribution(entry_id=root_entry_id, follow_up_id=fu.follow_up_id)
        db.add(contribution)
    contribution.follow_up_id = fu.follow_up_id
    contribution.minutes = float(finding.get("minutes") or 0.0)
    contribution.active = True
    contribution.updated_at = utc_now()
    db.flush()
    _recompute_site_delay(db, fu, zone_name)
    if old_fu is not None and old_fu.follow_up_id != fu.follow_up_id:
        _recompute_site_delay(db, old_fu, zone_name)
