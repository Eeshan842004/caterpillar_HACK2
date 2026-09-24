"""Console API contracts (technical spec §6.3)."""

from typing import Any, Literal

from pydantic import Field

from shiftmate.schemas.common import Role, StrictBaseModel


class ConsoleLoginRequest(StrictBaseModel):
    username: str
    password: str


class ConsoleUserResponse(StrictBaseModel):
    user_id: str
    username: str
    display_name: str
    role: Role
    site_ids: list[str]


class FollowUpSummary(StrictBaseModel):
    follow_up_id: str
    site_id: str
    category: str
    title: str
    summary: str
    priority: int
    status: str
    assigned_to: str | None = None
    machine_id: str | None = None
    zone_id: str | None = None
    reason_code: str | None = None
    metrics: dict[str, Any]
    first_seen_at: str
    last_seen_at: str


class FollowUpList(StrictBaseModel):
    items: list[FollowUpSummary]
    next_cursor: str | None = None


class Contribution(StrictBaseModel):
    entry_id: str
    minutes: float
    active: bool
    machine_id: str | None = None
    operator_display: str | None = None
    observed_at: str | None = None
    original_text: str | None = None


class Comment(StrictBaseModel):
    comment_id: str
    user_id: str
    text: str
    created_at: str


class FollowUpDetail(FollowUpSummary):
    contributions: list[Contribution]
    comments: list[Comment]
    related: dict[str, Any]
    resolved_at: str | None = None
    resolution_note: str | None = None


class AssignRequest(StrictBaseModel):
    user_id: str | None = None


class ResolveRequest(StrictBaseModel):
    note: str = Field(default="", max_length=500)


class CommentRequest(StrictBaseModel):
    text: str = Field(min_length=1, max_length=1000)


class IncidentSummary(StrictBaseModel):
    incident_id: str
    machine_id: str
    site_id: str
    zone_name: str | None = None
    occurred_at: str
    type: str | None = None
    severity: str | None = None
    status: str
    origin: str
    chain_ok: bool
    sent_to_trainer: bool
    scenario_id: str | None = None


class IncidentList(StrictBaseModel):
    items: list[IncidentSummary]
    next_cursor: str | None = None


class IncidentDetail(IncidentSummary):
    operator_display: str | None = None  # hidden (null) for trainers (§6.3)
    fields: dict[str, Any]
    snapshot: dict[str, Any] | None = None
    snapshot_complete: bool
    history: list[dict[str, Any]]


class IncidentReviewRequest(StrictBaseModel):
    field_corrections: dict[str, Any] = Field(default_factory=dict)
    note: str | None = Field(default=None, max_length=1000)


class IncidentReviewResponse(StrictBaseModel):
    incident: IncidentDetail
    scenario_id: str | None = None


class ReassignDecisionRequest(StrictBaseModel):
    decision: Literal["accept", "reject"]
    new_machine_id: str | None = None
    note: str | None = Field(default=None, max_length=500)


class HandoverItemResolveRequest(StrictBaseModel):
    note: str = Field(default="", max_length=500)


class HelpAnswerRequest(StrictBaseModel):
    answer_text: str = Field(min_length=1, max_length=1000)


# --- Scenarios (§6.3 C4, §5.4.3 published near-miss scenario, §8.23) ---


class ScenarioChoice(StrictBaseModel):
    text: str = Field(min_length=1, max_length=90)
    explanation: str = Field(min_length=1, max_length=200)


class ScenarioContent(StrictBaseModel):
    """One language's text of a scenario."""

    title: str = Field(min_length=1, max_length=120)
    situation: str = Field(min_length=1, max_length=600)
    choices: list[ScenarioChoice] = Field(min_length=3, max_length=3)
    correct_index: int = Field(ge=0, le=2)
    translation_status: Literal["draft", "final"] = "draft"


class ScenarioLocalized(StrictBaseModel):
    en: ScenarioContent
    hi: ScenarioContent | None = None


class ScenarioBody(StrictBaseModel):
    """Pack scenario shape (§5.4.3) + `source`, `source_site_id`, `localized`. Top-level text mirrors `localized.en`."""

    content_id: str
    kind: Literal["scenario"] = "scenario"
    title: str = Field(min_length=1, max_length=120)
    tags: list[str] = Field(default_factory=list)
    task_types: list[str] = Field(default_factory=list)
    duration_s: int = Field(default=90, ge=10, le=600)
    situation: str = Field(min_length=1, max_length=600)
    illustration: str | None = None
    choices: list[ScenarioChoice] = Field(min_length=3, max_length=3)
    correct_index: int = Field(ge=0, le=2)
    source: Literal["near_miss"] = "near_miss"
    source_site_id: str | None = None
    localized: ScenarioLocalized


class ScenarioUpdateRequest(StrictBaseModel):
    body: ScenarioBody


class ScenarioRejectRequest(StrictBaseModel):
    reason: str = Field(min_length=1, max_length=500)


class ScenarioRedraftRequest(StrictBaseModel):
    method: Literal["template", "llm"]


class ScenarioSummary(StrictBaseModel):
    scenario_id: str
    machine_class: str
    status: str
    draft_method: str
    title: str
    created_at: str
    source_incident_id: str | None = None


class ScenarioList(StrictBaseModel):
    items: list[ScenarioSummary]


class ScenarioDetail(ScenarioSummary):
    updated_at: str
    approved_at: str | None = None
    rejected_reason: str | None = None
    published_change_seq: int | None = None
    body: ScenarioBody
    source_summary: dict[str, Any]  # anonymised: type, object, place, time_of_day, zone_kind, conditions


class TaskReassignRequest(StrictBaseModel):
    new_machine_id: str | None = Field(default=None, pattern=r"^[A-Z]{2}-\d{2}$")
    note: str | None = Field(default=None, max_length=500)
