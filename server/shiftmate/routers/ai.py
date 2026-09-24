"""Device AI endpoints (technical spec §6.2 AI endpoints, §6.6; T40 / S1): incident extraction, handover wording,
free questions. Signed like every device call; 30/min per device; always 200 unless auth or validation fails.
With AI disabled, or on any failure, the answer is `{"method": "unavailable", "reason": ...}` and the device keeps
its rules/template result.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from shiftmate.ai import factcheck
from shiftmate.ai.client import MAX_FACTS_BYTES, AIClient, canonical_facts, get_ai_client
from shiftmate.ai.templates import PROMPTS
from shiftmate.config import settings
from shiftmate.db import get_db
from shiftmate.errors import ShiftMateException
from shiftmate.models import Device, Operator, Zone
from shiftmate.schemas.ai import (
    Answer,
    AskRequest,
    AskResponse,
    HandoverItemOut,
    HandoverWording,
    HandoverWordingRequest,
    HandoverWordingResponse,
    IncidentExtraction,
    IncidentExtractRequest,
    IncidentExtractResponse,
    Unavailable,
)
from shiftmate.security.device_auth import verify_device_auth
from shiftmate.security.ratelimit import ai_per_device

router = APIRouter(prefix="/ai", tags=["ai"])

MAX_TOKENS = {"incident_extract": 400, "handover_wording": 800, "ask": 300}


def _guard(facts: dict, device: Device) -> None:
    ai_per_device.hit(device.device_id)
    if len(canonical_facts(facts).encode("utf-8")) > MAX_FACTS_BYTES:
        raise ShiftMateException(status_code=422, code="validation_error", message="facts exceed 4 KB.")


def _names(db: Session) -> dict[str, list[str]]:
    return {
        "zone_names": [z.name for z in db.query(Zone).all()],
        "operator_names": [o.display_name for o in db.query(Operator).all()],
    }


def _client(request: Request) -> AIClient | None:
    return get_ai_client(request.app.state)


@router.post("/incident-extract", response_model=IncidentExtractResponse | Unavailable)
def incident_extract(
    req: IncidentExtractRequest,
    request: Request,
    db: Session = Depends(get_db),
    device: Device = Depends(verify_device_auth),
):
    _guard(req.facts, device)
    ai = _client(request)
    if ai is None:
        return Unavailable(reason="ai_disabled")
    prompt = PROMPTS["incident_extract"]
    facts = {**req.facts, "language": req.language, "rules_result": req.rules_result.model_dump(mode="json")}
    result = ai.call(
        prompt,
        facts,
        IncidentExtraction,
        max_tokens=MAX_TOKENS["incident_extract"],
        timeout=settings.AI_DEVICE_TIMEOUT_S,
        operator_text=req.text,
    )
    if not result.ok:
        return Unavailable(reason=result.reason, details=result.details or None)
    if factcheck.check_extraction(result.parsed, req.rules_result, facts, **_names(db)):
        return Unavailable(reason="fact_check_failed", details=result.details or None)
    return IncidentExtractResponse(
        fields=result.parsed, prompt_version=prompt.version, details=result.details or None
    )


@router.post("/handover-wording", response_model=HandoverWordingResponse | Unavailable)
def handover_wording(
    req: HandoverWordingRequest,
    request: Request,
    db: Session = Depends(get_db),
    device: Device = Depends(verify_device_auth),
):
    facts = {"language": req.language, "items": [i.model_dump(mode="json") for i in req.items]}
    _guard(facts, device)
    ai = _client(request)
    if ai is None:
        return Unavailable(reason="ai_disabled")
    prompt = PROMPTS["handover_wording"]
    result = ai.call(
        prompt,
        facts,
        HandoverWording,
        max_tokens=MAX_TOKENS["handover_wording"],
        timeout=settings.AI_DEVICE_TIMEOUT_S,
    )
    if not result.ok:
        return Unavailable(reason=result.reason)
    worded = {w.item_id: w.text for w in result.parsed.items}
    names = _names(db)
    out = []
    for item in req.items:  # per item: fact-check failure or a missing item → its template text
        text = worded.get(item.item_id)
        if text is None or factcheck.check_handover_item(text, item.facts, **names):
            out.append(HandoverItemOut(item_id=item.item_id, text=item.template_text, fallback=True))
        else:
            out.append(HandoverItemOut(item_id=item.item_id, text=text))
    return HandoverWordingResponse(items=out, prompt_version=prompt.version)


@router.post("/ask", response_model=AskResponse | Unavailable)
def ask(
    req: AskRequest,
    request: Request,
    db: Session = Depends(get_db),
    device: Device = Depends(verify_device_auth),
):
    _guard(req.facts, device)
    ai = _client(request)
    if ai is None:
        return Unavailable(reason="ai_disabled")
    prompt = PROMPTS["ask"]
    facts = {**req.facts, "language": req.language}
    result = ai.call(
        prompt,
        facts,
        Answer,
        max_tokens=MAX_TOKENS["ask"],
        timeout=settings.AI_DEVICE_TIMEOUT_S,
        operator_text=req.question,
    )
    if not result.ok:
        return Unavailable(reason=result.reason, details=result.details or None)
    if factcheck.check_text(result.parsed.answer, facts, **_names(db)):
        return Unavailable(reason="fact_check_failed", details=result.details or None)
    return AskResponse(
        answer=result.parsed.answer, prompt_version=prompt.version, details=result.details or None
    )
