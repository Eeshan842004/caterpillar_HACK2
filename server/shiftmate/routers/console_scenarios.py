"""Console scenarios (technical spec §6.3, C4; §8.23): list, detail, edit draft, approve, reject, redraft.

Supervisor, trainer and safety read (site-scoped, §9.2); only trainers write. Approval publishes a
`scenario.published` change to every device of the machine class.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from shiftmate.ai.client import get_ai_client
from shiftmate.config import settings
from shiftmate.db import get_db
from shiftmate.errors import ShiftMateException
from shiftmate.models import ConsoleUser, Incident, Scenario
from shiftmate.schemas.console import (
    ScenarioBody,
    ScenarioDetail,
    ScenarioList,
    ScenarioRedraftRequest,
    ScenarioRejectRequest,
    ScenarioSummary,
    ScenarioUpdateRequest,
)
from shiftmate.security.console_auth import require_role
from shiftmate.services import scenarios as svc
from shiftmate.services.ws_hub import notify
from shiftmate.time_util import iso_ms, utc_now

router = APIRouter(prefix="/console/scenarios", tags=["console_scenarios"])

readers = require_role("supervisor", "trainer", "safety")
trainer = require_role("trainer")


def _summary(s: Scenario) -> ScenarioSummary:
    return ScenarioSummary(
        scenario_id=s.scenario_id,
        machine_class=s.machine_class,
        status=s.status,
        draft_method=s.draft_method,
        title=s.body.get("title", ""),
        created_at=iso_ms(s.created_at),
        source_incident_id=s.source_incident_id,
    )


def _detail(db: Session, s: Scenario) -> ScenarioDetail:
    inc = db.get(Incident, s.source_incident_id) if s.source_incident_id else None
    return ScenarioDetail(
        **_summary(s).model_dump(),
        updated_at=iso_ms(s.updated_at),
        approved_at=iso_ms(s.approved_at) if s.approved_at else None,
        rejected_reason=s.rejected_reason,
        published_change_seq=s.published_change_seq,
        body=ScenarioBody.model_validate(s.body),
        source_summary=svc.source_summary(svc.incident_facts(db, inc)) if inc else {},
    )


def _load(db: Session, user: ConsoleUser, scenario_id: str) -> Scenario:
    s = db.get(Scenario, scenario_id)
    if s is None or s.site_id not in (user.site_ids or []):
        raise ShiftMateException(status_code=404, code="not_found", message="Scenario not found.")
    return s


def _require_status(s: Scenario, *allowed: str) -> None:
    if s.status not in allowed:
        raise ShiftMateException(
            status_code=409,
            code="invalid_state",
            message=f"Scenario is {s.status}; this needs {' or '.join(allowed)}.",
        )


@router.get("", response_model=ScenarioList)
def list_scenarios(
    status: str | None = Query(None, pattern="^(draft|approved|rejected)$"),
    db: Session = Depends(get_db),
    user: ConsoleUser = Depends(readers),
):
    q = db.query(Scenario).filter(Scenario.site_id.in_(user.site_ids or []))
    if status:
        q = q.filter(Scenario.status == status)
    return ScenarioList(
        items=[_summary(s) for s in q.order_by(Scenario.created_at.desc(), Scenario.scenario_id).all()]
    )


@router.get("/{scenario_id}", response_model=ScenarioDetail)
def get_scenario(scenario_id: str, db: Session = Depends(get_db), user: ConsoleUser = Depends(readers)):
    return _detail(db, _load(db, user, scenario_id))


@router.put("/{scenario_id}", response_model=ScenarioDetail)
def update_scenario(
    scenario_id: str,
    req: ScenarioUpdateRequest,
    db: Session = Depends(get_db),
    user: ConsoleUser = Depends(trainer),
):
    s = _load(db, user, scenario_id)
    _require_status(s, "draft")
    body = req.body.model_dump(mode="json")
    if body["content_id"] != s.scenario_id or body["source_site_id"] != s.body.get("source_site_id"):
        raise ShiftMateException(
            status_code=422, code="validation_error", message="content_id and source_site_id cannot change."
        )
    s.body = svc.normalise_body(body)
    s.updated_at, s.updated_by = utc_now(), user.user_id
    notify(db, s.site_id, ["scenarios"])
    db.commit()
    return _detail(db, s)


@router.post("/{scenario_id}/approve", response_model=ScenarioDetail)
def approve_scenario(scenario_id: str, db: Session = Depends(get_db), user: ConsoleUser = Depends(trainer)):
    s = _load(db, user, scenario_id)
    _require_status(s, "draft")
    svc.approve(db, s, user.user_id)
    notify(db, s.site_id, ["scenarios"])
    db.commit()
    return _detail(db, s)


@router.post("/{scenario_id}/reject", response_model=ScenarioDetail)
def reject_scenario(
    scenario_id: str,
    req: ScenarioRejectRequest,
    db: Session = Depends(get_db),
    user: ConsoleUser = Depends(trainer),
):
    s = _load(db, user, scenario_id)
    _require_status(s, "draft")
    s.status, s.rejected_reason, s.updated_at, s.updated_by = "rejected", req.reason, utc_now(), user.user_id
    notify(db, s.site_id, ["scenarios"])
    db.commit()
    return _detail(db, s)


@router.post("/{scenario_id}/redraft", response_model=ScenarioDetail)
def redraft_scenario(
    scenario_id: str,
    req: ScenarioRedraftRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: ConsoleUser = Depends(trainer),
):
    s = _load(db, user, scenario_id)
    _require_status(s, "draft", "rejected")
    if req.method == "llm":
        ai = get_ai_client(request.app.state)
        if ai is None:
            reason = "AI is disabled" if not settings.AI_ENABLED else "no API key is configured"
            raise ShiftMateException(
                status_code=409, code="invalid_state", message=f"AI unavailable: {reason}."
            )
        svc.llm_redraft(db, s, user.user_id, ai)  # falls back to the template on any AI failure
    else:
        svc.redraft(db, s, user.user_id)
    notify(db, s.site_id, ["scenarios"])
    db.commit()
    return _detail(db, s)
