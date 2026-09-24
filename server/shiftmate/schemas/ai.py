"""Language AI contracts (technical spec §6.2 AI endpoints, §6.6; T40 / S1).

Model outputs are parsed into the `*Output` models (`extra="forbid"`); anything that fails to parse, fails the fact
check or errors becomes `{"method": "unavailable", "reason": ...}` and the caller keeps its template.
"""

from typing import Any, Literal

from pydantic import Field

from shiftmate.schemas.common import IncidentType, ObjectType, Place, Severity, StrictBaseModel

Language = Literal["en", "hi"]
UnavailableReason = Literal[
    "ai_disabled", "timeout", "provider_error", "invalid_output", "fact_check_failed", "refused"
]

# --- Structured model outputs (§6.6) ---


class IncidentExtraction(StrictBaseModel):
    no_incident: bool
    type: IncidentType | None = None
    object: ObjectType | None = None
    place: Place | None = None
    contact: Literal["yes", "no", "unknown"]
    severity_suggestion: Severity | None = None
    summary: str = Field(max_length=160)


class WordedItem(StrictBaseModel):
    item_id: str
    text: str = Field(max_length=200)


class HandoverWording(StrictBaseModel):
    items: list[WordedItem]


class Answer(StrictBaseModel):
    answer: str = Field(max_length=250)
    used_fact_keys: list[str]


class DraftChoice(StrictBaseModel):
    text: str = Field(max_length=90)
    explanation: str = Field(max_length=200)


class ScenarioDraft(StrictBaseModel):
    title: str = Field(max_length=60)
    situation: str = Field(max_length=300)
    choices: list[DraftChoice] = Field(min_length=3, max_length=3)
    correct_index: int = Field(ge=0, le=2)


# --- Endpoint requests / responses (§6.2) ---


class RulesResult(StrictBaseModel):
    no_incident: bool = False
    type: IncidentType | None = None
    object: ObjectType | None = None
    place: Place | None = None
    contact: Literal["yes", "no", "unknown"] | None = None


class IncidentExtractRequest(StrictBaseModel):
    incident_id: str
    language: Language
    text: str = Field(max_length=2000)
    facts: dict[str, Any]
    rules_result: RulesResult


class HandoverWordingItemIn(StrictBaseModel):
    item_id: str
    item_type: str
    facts: dict[str, Any]
    template_text: str = Field(max_length=500)


class HandoverWordingRequest(StrictBaseModel):
    language: Language
    items: list[HandoverWordingItemIn] = Field(min_length=1, max_length=20)


class AskRequest(StrictBaseModel):
    language: Language
    question: str = Field(min_length=1, max_length=2000)
    facts: dict[str, Any]


class Unavailable(StrictBaseModel):
    method: Literal["unavailable"] = "unavailable"
    reason: UnavailableReason
    details: dict[str, Any] | None = None


class IncidentExtractResponse(StrictBaseModel):
    method: Literal["llm"] = "llm"
    fields: IncidentExtraction
    prompt_version: str
    details: dict[str, Any] | None = None


class HandoverItemOut(StrictBaseModel):
    item_id: str
    text: str
    fallback: bool = False


class HandoverWordingResponse(StrictBaseModel):
    method: Literal["llm"] = "llm"
    items: list[HandoverItemOut]
    prompt_version: str


class AskResponse(StrictBaseModel):
    method: Literal["llm"] = "llm"
    answer: str
    prompt_version: str
    details: dict[str, Any] | None = None
