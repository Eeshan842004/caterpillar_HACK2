"""Console incidents (technical spec §6.3, C3): site-scoped list/detail, safety review, send to trainer."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from shiftmate.db import get_db
from shiftmate.errors import ShiftMateException
from shiftmate.models import ConsoleUser, Incident, LedgerEntry, Operator, Zone
from shiftmate.schemas.common import IncidentType, ObjectType, Place, Severity
from shiftmate.schemas.console import (
    IncidentDetail,
    IncidentList,
    IncidentReviewRequest,
    IncidentReviewResponse,
    IncidentSummary,
)
from shiftmate.security.console_auth import require_role
from shiftmate.services.changes import record_change
from shiftmate.services.console_actions import decode_cursor, encode_cursor, server_entry
from shiftmate.time_util import iso_ms, utc_now

router = APIRouter(prefix="/console/incidents", tags=["console_incidents"])

REVIEWABLE = {"type": IncidentType, "severity": Severity, "object": ObjectType, "place": Place}


def _zone_name(db: Session, zone_id: str | None) -> str | None:
    zone = db.get(Zone, zone_id) if zone_id else None
    return zone.name if zone else zone_id


def _summary(db: Session, inc: Incident) -> IncidentSummary:
    return IncidentSummary(
        incident_id=inc.incident_id, machine_id=inc.machine_id, site_id=inc.site_id, zone_name=_zone_name(db, inc.zone_id),
        occurred_at=iso_ms(inc.occurred_at), type=inc.type, severity=inc.severity, status=inc.status, origin=inc.origin,
        chain_ok=inc.chain_ok, sent_to_trainer=inc.sent_to_trainer, scenario_id=inc.scenario_id,
    )


def _detail(db: Session, inc: Incident, user: ConsoleUser) -> IncidentDetail:
    history = []
    for e in db.query(LedgerEntry).filter(LedgerEntry.machine_id == inc.machine_id).order_by(LedgerEntry.recorded_at).all():
        body = e.payload.get("replacement") if e.kind == "correction" else e.payload
        if (body or {}).get("incident_id") == inc.incident_id:
            history.append({"entry_id": e.entry_id, "kind": e.kind, "subtype": e.subtype, "source": e.source,
                            "recorded_at": iso_ms(e.recorded_at),
                            "original_text": None if user.role == "trainer" else e.original_text})
    op = db.get(Operator, inc.operator_id) if inc.operator_id else None
    return IncidentDetail(
        **_summary(db, inc).model_dump(),
        operator_display=None if user.role == "trainer" else (op.display_name if op else None),
        fields=inc.fields or {}, snapshot=inc.snapshot, snapshot_complete=inc.snapshot_complete, history=history,
    )


def _load(db: Session, user: ConsoleUser, incident_id: str) -> Incident:
    inc = db.get(Incident, incident_id)
    if inc is None or inc.site_id not in (user.site_ids or []):    # site guard (audit: cross-site leak)
        raise ShiftMateException(status_code=404, code="not_found", message="Incident not found.")
    return inc


@router.get("", response_model=IncidentList)
def list_incidents(
    status: str | None = None,
    type: str | None = None,
    cursor: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: ConsoleUser = Depends(require_role("safety", "supervisor", "trainer")),
):
    q = db.query(Incident).filter(Incident.site_id.in_(user.site_ids or []))
    if status:
        q = q.filter(Incident.status == status)
    if type:
        q = q.filter(Incident.type == type)
    if cursor:
        occurred, iid = decode_cursor(cursor)
        occurred_dt = datetime.fromisoformat(occurred)
        q = q.filter(or_(Incident.occurred_at < occurred_dt,
                         and_(Incident.occurred_at == occurred_dt, Incident.incident_id < iid)))
    rows = q.order_by(Incident.occurred_at.desc(), Incident.incident_id.desc()).limit(limit + 1).all()
    page = rows[:limit]
    nxt = encode_cursor([page[-1].occurred_at.isoformat(), page[-1].incident_id]) if len(rows) > limit else None
    return IncidentList(items=[_summary(db, r) for r in page], next_cursor=nxt)


@router.get("/{incident_id}", response_model=IncidentDetail)
def get_incident(incident_id: str, db: Session = Depends(get_db),
                 user: ConsoleUser = Depends(require_role("safety", "supervisor", "trainer"))):
    return _detail(db, _load(db, user, incident_id), user)


@router.post("/{incident_id}/review", response_model=IncidentReviewResponse)
def review_incident(incident_id: str, req: IncidentReviewRequest, db: Session = Depends(get_db),
                    user: ConsoleUser = Depends(require_role("safety"))):
    inc = _load(db, user, incident_id)
    corrections = {}
    for name, value in (req.field_corrections or {}).items():
        if name == "contact":
            if value not in ("yes", "no", "unknown"):
                raise ShiftMateException(status_code=422, code="validation_error", message="contact must be yes/no/unknown")
        elif name in REVIEWABLE:
            REVIEWABLE[name](value)            # raises ValueError on an invalid enum value
        else:
            raise ShiftMateException(status_code=422, code="validation_error", message=f"{name} cannot be corrected")
        corrections[name] = value

    entry = server_entry(db, user, kind="incident", subtype="reviewed", machine_id=inc.machine_id, audience="safety",
                         payload={"incident_id": inc.incident_id, "field_corrections": corrections, "note": req.note})
    fields = dict(inc.fields or {})
    for name, value in corrections.items():
        fields[name] = {"value": value, "source": "reviewed", "entry_id": entry.entry_id}
    inc.fields = fields
    inc.type = (fields.get("type") or {}).get("value")
    inc.severity = (fields.get("severity") or {}).get("value")
    inc.status, inc.reviewed_by, inc.reviewed_at, inc.review_note, inc.updated_at = (
        "reviewed", user.user_id, utc_now(), req.note, utc_now())
    record_change(db, "incident.reviewed", "machine", inc.machine_id,
                  {"incident_id": inc.incident_id, "reviewed_at": iso_ms(inc.reviewed_at), "field_corrections": corrections})
    db.commit()
    # Scenario drafting from a reviewed near-miss is task T31 (§8.23); not built yet, so no draft id is returned.
    return IncidentReviewResponse(incident=_detail(db, inc, user), scenario_id=inc.scenario_id)


@router.post("/{incident_id}/send-to-trainer", response_model=IncidentDetail)
def send_to_trainer(incident_id: str, db: Session = Depends(get_db),
                    user: ConsoleUser = Depends(require_role("safety", "supervisor"))):
    inc = _load(db, user, incident_id)
    inc.sent_to_trainer = True
    inc.updated_at = utc_now()
    db.commit()
    return _detail(db, inc, user)
