from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from shiftmate.schemas.common import (
    AlertLevel,
    AlertType,
    Audience,
    BlockReason,
    IdleCategory,
    IdleClass,
    IdleReason,
    IncidentType,
    LedgerKind,
    ObjectType,
    Place,
    ReassignReason,
    Severity,
    Source,
    StrictBaseModel,
    SyncStatus,
    Unit,
)


class ShiftEventStartPayload(StrictBaseModel):
    auth_method: str  # 'pin' | 'fob_sim'
    language: str
    guidance: str  # 'guided' | 'concise'
    profile_id: str
    profile_version: int


class ShiftEventEndPayload(StrictBaseModel):
    handover_id: str | None = None


class SignalSummary5mPayload(StrictBaseModel):
    window_start: int
    window_end: int
    engine_on_s: int
    secured_s: int
    ready_s: int
    working_s: int
    travelling_s: int
    unknown_s: int
    idle_s: int
    fuel_used_l: float | None = None
    load_cycles: int | None = None
    max_speed_kmh: float | None = None
    avg_load_factor_pct: float | None = None
    belt_unfastened_moving_s: int | None = None
    samples: int
    missing_samples: int
    missing_signal_names: list[str]


class ConditionForecastPayload(StrictBaseModel):
    site_id: str
    valid_from: str
    valid_to: str
    weather: str
    visibility: str
    visibility_m: float | None = None
    temp_c: float
    heat_index_c: float | None = None
    wind_kmh: float
    precipitation_mm: float
    issued_at: str
    source: str  # 'seed' | 'open_meteo' | 'sim_weather'


class IdleReasonPayload(StrictBaseModel):
    idle_event_id: str
    reason_code: IdleReason
    free_text: str | None = None
    via: str = "button"  # 'button' | 'voice'


class ConditionReportPayload(StrictBaseModel):
    condition: str
    active: bool


class IncidentReportPayload(StrictBaseModel):
    incident_id: str
    type: IncidentType
    object: ObjectType
    place: Place
    contact: str  # 'yes' | 'no' | 'unknown'
    severity: Severity
    via: str = "button"


class ProgressReportPayload(StrictBaseModel):
    task_id: str
    progress_qty: float
    unit: Unit


class HandoverNotePayload(StrictBaseModel):
    handover_id: str
    item_id: str
    text: str
    via: str = "button"


class HelpRequestPayload(StrictBaseModel):
    content_id: str
    question_text: str | None = None


class ReassignmentRequestPayload(StrictBaseModel):
    task_id: str
    reason_code: ReassignReason
    impact: dict[str, Any] | None = None


class SupervisorNotificationPayload(StrictBaseModel):
    task_id: str
    reason_code: str
    source_entry_id: str
    impact: dict[str, Any]


class AlertFeedbackPayload(StrictBaseModel):
    alert_id: str
    alert_type: AlertType
    feedback: str  # 'wrong' | 'annoying'


class RecommendationFeedbackPayload(StrictBaseModel):
    rec_id: str
    content_id: str
    pattern_code: str | None = None
    feedback: str = "not_relevant"


class IdleClassificationPayload(StrictBaseModel):
    idle_event_id: str
    idle_class: IdleClass
    required_s: int
    non_required_s: int
    category: IdleCategory | None = None


class EstimatePayload(StrictBaseModel):
    task_id: str
    task_type: str
    basis: str
    baseline_min: float
    p10_min: float
    p50_min: float
    p90_min: float
    expected_wait_min: float
    factors: list[dict[str, Any]]
    artifact_id: str
    personal_offset: float | None = None
    context: dict[str, Any]


class AlertTransitionPayload(StrictBaseModel):
    alert_id: str
    alert_type: AlertType
    level: AlertLevel
    group_key: str
    zone_id: str | None = None
    object_id: str | None = None
    object_type: ObjectType | None = None
    place: Place | None = None
    distance_m: float | None = None
    ttc_s: float | None = None
    multiplier: float | None = None
    occurrences: int = 1
    clear_reason: str | None = None
    safe_exit: dict[str, Any] | None = None


class IncidentCreatedPayload(StrictBaseModel):
    incident_id: str
    origin: str  # 'auto' | 'operator'
    trigger_alert_id: str | None = None
    occurred_at: str
    zone_id: str | None = None
    observed: dict[str, Any]
    snapshot: dict[str, Any]
    snapshot_complete: bool = False
    severity_default: Severity


class IncidentSnapshotCompletedPayload(StrictBaseModel):
    incident_id: str
    post_samples: list[dict[str, Any]]
    truncated: bool = False


class IncidentStatusChangedPayload(StrictBaseModel):
    incident_id: str
    status: str  # 'awaiting_report' | 'reported'


class TaskEventPayload(StrictBaseModel):
    task_id: str
    assignment_revision: int
    reason_code: BlockReason | None = None
    output_qty: float | None = None
    actual_start: str | None = None
    actual_end: str | None = None
    active_min: float | None = None
    waiting_min: float | None = None
    break_min: float | None = None
    paused_min: float | None = None


class IdleEventStartedPayload(StrictBaseModel):
    idle_event_id: str
    candidate_started_at: str
    task_id: str | None = None
    zone_id: str | None = None


class IdleEventEndedPayload(StrictBaseModel):
    idle_event_id: str
    ended_at: str
    duration_s: int
    required_s: int


class HandoverItemAddedPayload(StrictBaseModel):
    handover_id: str
    item_id: str
    item_type: str
    text_key: str | None = None
    text_params: dict[str, Any] | None = None
    text: str
    audiences: list[Audience]
    source_entry_ids: list[str] = Field(default_factory=list)
    task_id: str | None = None
    incident_id: str | None = None
    carried_from_item_id: str | None = None


class HandoverItemRemovedPayload(StrictBaseModel):
    item_id: str
    reason: Literal["resolved", "not_relevant", "duplicate"]


class HandoverItemEditedPayload(StrictBaseModel):
    item_id: str
    text: str


class HandoverItemAcknowledgedPayload(StrictBaseModel):
    item_id: str


class HandoverItemResolvedPayload(StrictBaseModel):
    item_id: str
    by: Literal["task_completed"]


class LearningEventPayload(StrictBaseModel):
    content_id: str
    mode: str = "full"  # 'full' | 'refresher'
    question_index: int | None = None
    choice_index: int | None = None
    correct: bool | None = None
    refresher_opt_in: bool | None = None
    review_step: int | None = None


class CorrectionPayload(StrictBaseModel):
    target_kind: LedgerKind
    target_subtype: str
    replacement: dict[str, Any] | None = None


class LedgerEntryWire(StrictBaseModel):
    entry_id: str
    device_id: str | None = None
    shift_id: str | None = None
    machine_id: str
    operator_id: str | None = None
    kind: LedgerKind
    subtype: str
    source: Source
    payload: dict[str, Any]
    observed_at: str
    recorded_at: str
    freshness_s: float | None = None
    confidence: str | None = None
    rule_or_model_version: str | None = None
    original_text: str | None = None
    supersedes: str | None = None
    audience: Audience
    data_origin: str
    sync_status: SyncStatus = SyncStatus.confirmed
    chain_seq: int | None = None
    prev_hash: str | None = None
    content_hash: str | None = None
    canonical_payload: str | None = None


# --- Payload models added to cover every kind/subtype in technical spec §5.3.2 ---


class MachineStateChangePayload(StrictBaseModel):
    from_state: str = Field(alias="from")
    to: str
    reason: str

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class FindingObserved(StrictBaseModel):
    text_key: str
    params: dict[str, Any] = Field(default_factory=dict)


class FindingPayload(StrictBaseModel):
    """`Finding` (§8.8)."""

    finding_id: str
    subject_id: str
    pattern_code: Literal[
        "required_idle",
        "idle_reported_wait",
        "unexplained_idle_repeat",
        "overspeed_repeat",
        "overspeed_zone_multi_operator",
        "fuel_per_cycle_high",
        "belt_repeat_operating",
        "belt_switch_flapping",
        "sensor_unavailable_persistent",
        "near_miss_cluster",
    ]
    owner: Literal["nobody", "operator", "site", "machine", "needs_review"]
    evidence_status: Literal["reported", "corroborated", "unresolved", "insufficient_evidence"]
    reason_key: str
    observed: FindingObserved
    possible_explanations: list[str]
    related_entry_ids: list[str]
    machine_id: str
    site_id: str
    zone_id: str | None = None
    reason_code: IdleReason | None = None
    minutes: float | None = None
    local_date: str
    rule_version: str


class RecommendationPayload(StrictBaseModel):
    rec_id: str
    content_id: str
    source: Literal["task_prep", "condition_prep", "pattern", "published_near_miss", "replay", "refresher"]
    pattern_code: str | None = None
    condition: Literal["rain", "dust", "darkness"] | None = None
    reason_key: str
    reason_params: dict[str, Any] = Field(default_factory=dict)


class IncidentExtractionPayload(StrictBaseModel):
    incident_id: str
    method: Literal["rules", "llm"]
    fields: dict[str, Any]
    no_incident: bool


class SiteTipPayload(StrictBaseModel):
    tip_id: str
    task_type: str | None = None
    zone_id: str | None = None
    upload_entry_id: str
    duration_s: float


class AlertReviewedPayload(StrictBaseModel):
    alert_id: str
    alert_type: AlertType
    follow_up_id: str
    note: str | None = None


class IncidentReviewedPayload(StrictBaseModel):
    incident_id: str
    field_corrections: dict[str, Any] = Field(default_factory=dict)
    note: str | None = None


PAYLOAD_MODELS: dict[tuple[str, str], type[BaseModel]] = {
    ("shift_event", "start"): ShiftEventStartPayload,
    ("shift_event", "end"): ShiftEventEndPayload,
    ("observation", "signal_summary_5m"): SignalSummary5mPayload,
    ("observation", "condition_forecast"): ConditionForecastPayload,
    ("report", "idle_reason"): IdleReasonPayload,
    ("report", "condition_report"): ConditionReportPayload,
    ("report", "incident_report"): IncidentReportPayload,
    ("report", "progress_report"): ProgressReportPayload,
    ("report", "handover_note"): HandoverNotePayload,
    ("report", "help_request"): HelpRequestPayload,
    ("report", "reassignment_request"): ReassignmentRequestPayload,
    ("report", "supervisor_notification"): SupervisorNotificationPayload,
    ("report", "alert_feedback"): AlertFeedbackPayload,
    ("report", "recommendation_feedback"): RecommendationFeedbackPayload,
    ("report", "site_tip"): SiteTipPayload,
    ("inference", "machine_state_change"): MachineStateChangePayload,
    ("inference", "idle_classification"): IdleClassificationPayload,
    ("inference", "finding"): FindingPayload,
    ("inference", "estimate"): EstimatePayload,
    ("inference", "incident_extraction"): IncidentExtractionPayload,
    ("inference", "recommendation"): RecommendationPayload,
    ("alert", "raised"): AlertTransitionPayload,
    ("alert", "escalated"): AlertTransitionPayload,
    ("alert", "acknowledged"): AlertTransitionPayload,
    ("alert", "cleared"): AlertTransitionPayload,
    ("alert", "reviewed"): AlertReviewedPayload,
    ("incident", "created"): IncidentCreatedPayload,
    ("incident", "snapshot_completed"): IncidentSnapshotCompletedPayload,
    ("incident", "status_changed"): IncidentStatusChangedPayload,
    ("incident", "reviewed"): IncidentReviewedPayload,
    ("idle_event", "started"): IdleEventStartedPayload,
    ("idle_event", "ended"): IdleEventEndedPayload,
    ("handover_item", "added"): HandoverItemAddedPayload,
    ("handover_item", "removed"): HandoverItemRemovedPayload,
    ("handover_item", "edited"): HandoverItemEditedPayload,
    ("handover_item", "acknowledged"): HandoverItemAcknowledgedPayload,
    ("handover_item", "resolved"): HandoverItemResolvedPayload,
}
for _st in ("start", "pause", "resume", "block", "complete", "cancel"):
    PAYLOAD_MODELS[("task_event", _st)] = TaskEventPayload
for _st in ("started", "answered", "completed", "deferred"):
    PAYLOAD_MODELS[("learning_event", _st)] = LearningEventPayload

# Kinds whose entries must carry rule_or_model_version (§5.3.1, NFR-15)
VERSIONED_KINDS = {"alert", "inference"}
# Server-authored subtypes that a device may never push (§5.3.2)
SERVER_ONLY = {("alert", "reviewed"), ("incident", "reviewed")}


class PayloadError(ValueError):
    pass


def validate_ledger_payload(kind: str, subtype: str, payload: dict[str, Any]) -> None:
    """Validates one ledger payload against §5.3.2. Raises PayloadError with a readable reason."""
    if kind == "correction":
        try:
            corr = CorrectionPayload.model_validate(payload)
        except ValidationError as exc:
            raise PayloadError(f"correction/{subtype}: {exc.errors()[0]['msg']}") from exc
        if corr.target_subtype != subtype:
            raise PayloadError(f"correction/{subtype}: target_subtype must equal the entry subtype")
        if corr.replacement is not None:
            validate_ledger_payload(corr.target_kind.value, corr.target_subtype, corr.replacement)
        return
    model = PAYLOAD_MODELS.get((kind, subtype))
    if model is None:
        raise PayloadError(f"unknown kind/subtype {kind}/{subtype}")
    try:
        model.model_validate(payload)
    except ValidationError as exc:
        err = exc.errors()[0]
        loc = ".".join(str(x) for x in err["loc"])
        raise PayloadError(f"{kind}/{subtype}: {loc}: {err['msg']}") from exc
