"""Server data model — technical spec §5.2.

Runs on SQLite for local development and on PostgreSQL 16 in the site-server deployment; every column,
CHECK constraint and (partial) unique index below mirrors the §5.2 DDL. Timestamps are stored as naive UTC.
"""

import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from shiftmate.db import Base
from shiftmate.time_util import utc_now


def _uuid() -> str:
    return str(uuid.uuid4())


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


AUDIENCES = ("next_operator", "site", "trainer", "safety")  # operator_only never reaches the server
SOURCES = ("observed", "reported", "inferred", "reviewed")
ROLES = ("supervisor", "trainer", "safety", "mechanic")
FOLLOW_UP_CATEGORIES = (
    "site_delay",
    "machine_check",
    "safety_incident",
    "help_request",
    "assignment_request",
    "supervisor_notification",
    "sync_conflict",
    "near_miss_cluster",
    "overspeed_zone",
    "alert_review",
    "usage_review",
    "sos",
    "chain_integrity",
)
EXEC_STATES = ("PLANNED", "ACTIVE", "PAUSED", "BLOCKED", "COMPLETED", "CANCELLED")


class Site(Base):
    __tablename__ = "sites"
    __table_args__ = (
        CheckConstraint(_in("sector", ("construction", "mining")), name="ck_sites_sector"),
        CheckConstraint(_in("congestion_level", ("low", "medium", "high")), name="ck_sites_congestion"),
        CheckConstraint(
            "job_efficiency_override IS NULL OR (job_efficiency_override > 0 AND job_efficiency_override <= 1)",
            name="ck_sites_job_efficiency",
        ),
    )

    site_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    sector = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    utc_offset_minutes = Column(Integer, nullable=False, default=330)
    diesel_price_inr_per_l = Column(Float, nullable=False, default=92.00)
    dark_start_local = Column(String, nullable=False, default="19:00")
    dark_end_local = Column(String, nullable=False, default="06:00")
    job_efficiency_override = Column(Float, nullable=True)
    congestion_level = Column(String, nullable=False, default="medium")
    data_origin = Column(String, nullable=False, default="demo_seed")
    created_at = Column(DateTime, nullable=False, default=utc_now)

    zones = relationship("Zone", back_populates="site", cascade="all, delete-orphan")


class Zone(Base):
    __tablename__ = "zones"
    __table_args__ = (
        CheckConstraint(
            _in(
                "kind",
                ("trench_area", "loading_bay", "yard", "haul_road", "shovel", "crusher", "dump", "other"),
            ),
            name="ck_zones_kind",
        ),
        CheckConstraint("radius_m > 0", name="ck_zones_radius"),
        Index("zones_site", "site_id"),
    )

    zone_id = Column(String, primary_key=True)
    site_id = Column(String, ForeignKey("sites.site_id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    radius_m = Column(Float, nullable=False)
    speed_limit_kmh = Column(Float, nullable=True)

    site = relationship("Site", back_populates="zones")


class MachineProfile(Base):
    __tablename__ = "machine_profiles"

    profile_id = Column(String, primary_key=True)
    version = Column(Integer, primary_key=True)
    machine_class = Column(String, nullable=False)
    body = Column(JSON, nullable=False)
    published_at = Column(DateTime, nullable=False, default=utc_now)


class Machine(Base):
    __tablename__ = "machines"
    __table_args__ = (
        CheckConstraint("short_id BETWEEN 1 AND 65535", name="ck_machines_short_id"),
        CheckConstraint(_in("detail_level", ("detailed", "status_only")), name="ck_machines_detail"),
    )

    machine_id = Column(String, primary_key=True)
    short_id = Column(Integer, unique=True, nullable=False)
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    profile_id = Column(String, nullable=False)
    profile_version = Column(Integer, nullable=False)
    model_name = Column(String, nullable=False)
    year_of_manufacture = Column(Integer, nullable=False)
    detail_level = Column(String, nullable=False)
    data_origin = Column(String, nullable=False, default="demo_seed")
    created_at = Column(DateTime, nullable=False, default=utc_now)


class Operator(Base):
    __tablename__ = "operators"
    __table_args__ = (
        CheckConstraint(_in("language", ("en", "hi", "ta")), name="ck_operators_language"),
        CheckConstraint(
            _in("skill_level", ("beginner", "intermediate", "expert")), name="ck_operators_skill"
        ),
        CheckConstraint("experience_months >= 0", name="ck_operators_experience"),
    )

    operator_id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    language = Column(String, nullable=False)
    skill_level = Column(String, nullable=False)
    experience_months = Column(Integer, nullable=False, default=0)
    hired_at = Column(Date, nullable=False)
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    pin_salt = Column(String(32), nullable=False)
    pin_hash = Column(String(64), nullable=False)
    pin_iterations = Column(Integer, nullable=False, default=20000)
    data_origin = Column(String, nullable=False, default="demo_seed")
    updated_at = Column(DateTime, nullable=False, default=utc_now)


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(String, primary_key=True, default=_uuid)
    label = Column(String, nullable=False)
    machine_id = Column(String, ForeignKey("machines.machine_id"), nullable=False)
    paired_at = Column(DateTime, nullable=False, default=utc_now)
    last_seen_at = Column(DateTime, nullable=True)
    last_push_at = Column(DateTime, nullable=True)
    last_pull_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)


class PairingCode(Base):
    __tablename__ = "pairing_codes"

    code = Column(String(6), primary_key=True)
    machine_id = Column(String, ForeignKey("machines.machine_id"), nullable=False)
    reusable = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    used_by_device_id = Column(String, nullable=True)


class ConsoleUser(Base):
    __tablename__ = "console_users"
    __table_args__ = (CheckConstraint(_in("role", ROLES), name="ck_console_users_role"),)

    user_id = Column(String, primary_key=True, default=_uuid)
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    site_ids = Column(JSON, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    disabled_at = Column(DateTime, nullable=True)


class ConsoleSession(Base):
    __tablename__ = "console_sessions"

    session_id = Column(String(43), primary_key=True)
    user_id = Column(String, ForeignKey("console_users.user_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)


class Shift(Base):
    __tablename__ = "shifts"

    shift_id = Column(String, primary_key=True, default=_uuid)
    machine_id = Column(String, ForeignKey("machines.machine_id"), nullable=False)
    operator_id = Column(String, ForeignKey("operators.operator_id"), nullable=False)
    device_id = Column(String, ForeignKey("devices.device_id"), nullable=True)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint(_in("source", SOURCES), name="ck_ledger_source"),
        CheckConstraint(
            "confidence IS NULL OR " + _in("confidence", ("high", "medium", "low")),
            name="ck_ledger_confidence",
        ),
        CheckConstraint(_in("audience", AUDIENCES), name="ck_ledger_audience"),
        CheckConstraint(_in("review_status", ("ok", "needs_review")), name="ck_ledger_review"),
        Index("ledger_machine_time", "machine_id", "observed_at"),
        Index("ledger_kind", "kind", "subtype"),
        Index("ledger_supersedes", "supersedes"),
        Index(
            "ledger_chain",
            "device_id",
            "chain_seq",
            unique=True,
            sqlite_where=text("chain_seq IS NOT NULL"),
            postgresql_where=text("chain_seq IS NOT NULL"),
        ),
    )

    entry_id = Column(String, primary_key=True, default=_uuid)
    device_id = Column(String, ForeignKey("devices.device_id"), nullable=True)
    author_user_id = Column(String, ForeignKey("console_users.user_id"), nullable=True)
    shift_id = Column(String, nullable=True)
    machine_id = Column(String, nullable=False)
    operator_id = Column(String, nullable=True)
    kind = Column(String, nullable=False)
    subtype = Column(String, nullable=False)
    source = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    observed_at = Column(DateTime, nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    received_at = Column(DateTime, nullable=False, default=utc_now)
    freshness_s = Column(Float, nullable=True)
    confidence = Column(String, nullable=True)
    rule_or_model_version = Column(String, nullable=True)
    original_text = Column(String, nullable=True)
    supersedes = Column(String, nullable=True)
    audience = Column(String, nullable=False)
    data_origin = Column(String, nullable=False)
    payload_sha256 = Column(String(64), nullable=False)
    chain_seq = Column(Integer, nullable=True)
    prev_hash = Column(String(64), nullable=True)
    content_hash = Column(String(64), nullable=True)
    canonical_payload = Column(String, nullable=True)
    review_status = Column(String, nullable=False, default="ok")
    review_reason = Column(String, nullable=True)


class TaskAssignment(Base):
    __tablename__ = "task_assignments"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_tasks_quantity"),
        CheckConstraint(_in("unit", ("m", "m2", "m3", "t", "loads", "lifts")), name="ck_tasks_unit"),
        CheckConstraint("priority BETWEEN 1 AND 3", name="ck_tasks_priority"),
        CheckConstraint("planned_start_window_min BETWEEN 0 AND 240", name="ck_tasks_window"),
        CheckConstraint(_in("source", ("dispatcher", "seed", "reassignment")), name="ck_tasks_source"),
        CheckConstraint(_in("status", ("assigned", "cancelled")), name="ck_tasks_status"),
        CheckConstraint(_in("exec_state", EXEC_STATES), name="ck_tasks_exec_state"),
        Index("tasks_machine_date", "machine_id", "planned_date"),
    )

    task_id = Column(String, primary_key=True)
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    machine_id = Column(String, ForeignKey("machines.machine_id"), nullable=True)
    task_type = Column(String, nullable=False)
    zone_id = Column(String, ForeignKey("zones.zone_id"), nullable=True)
    location_text = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    material = Column(String, nullable=False)
    priority = Column(Integer, nullable=False, default=2)
    completion_criterion = Column(String, nullable=False)
    planner_minutes = Column(Float, nullable=True)
    planned_date = Column(Date, nullable=False)
    planned_start_at = Column(DateTime, nullable=True)
    planned_start_window_min = Column(Integer, nullable=False, default=15)
    sequence = Column(Integer, nullable=False)
    source = Column(String, nullable=False, default="seed")
    revision = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="assigned")
    exec_state = Column(String, nullable=False, default="PLANNED")
    exec_updated_at = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    active_min = Column(Float, nullable=True)
    waiting_min = Column(Float, nullable=True)
    output_qty = Column(Float, nullable=True)
    data_origin = Column(String, nullable=False, default="demo_seed")
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now)


class ReassignmentRequest(Base):
    __tablename__ = "reassignment_requests"
    __table_args__ = (
        CheckConstraint(_in("status", ("pending", "accepted", "rejected")), name="ck_reassign_status"),
    )

    request_id = Column(String, primary_key=True)  # = ledger entry_id of report/reassignment_request
    task_id = Column(String, ForeignKey("task_assignments.task_id"), nullable=False)
    machine_id = Column(String, nullable=False)
    operator_id = Column(String, nullable=False)
    reason_code = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    decided_by = Column(String, ForeignKey("console_users.user_id"), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    new_machine_id = Column(String, nullable=True)
    decision_note = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)


class FollowUp(Base):
    __tablename__ = "follow_ups"
    __table_args__ = (
        CheckConstraint(_in("category", FOLLOW_UP_CATEGORIES), name="ck_follow_ups_category"),
        CheckConstraint("priority BETWEEN 0 AND 3", name="ck_follow_ups_priority"),
        CheckConstraint(_in("status", ("open", "assigned", "resolved")), name="ck_follow_ups_status"),
        Index(
            "follow_ups_open_group",
            "group_key",
            unique=True,
            sqlite_where=text("status <> 'resolved'"),
            postgresql_where=text("status <> 'resolved'"),
        ),
        Index("follow_ups_list", "site_id", "status", "priority", "first_seen_at"),
    )

    follow_up_id = Column(String, primary_key=True, default=_uuid)
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    category = Column(String, nullable=False)
    group_key = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="open")
    assigned_to = Column(String, ForeignKey("console_users.user_id"), nullable=True)
    machine_id = Column(String, nullable=True)
    zone_id = Column(String, nullable=True)
    reason_code = Column(String, nullable=True)
    related_id = Column(String, nullable=True)
    metrics = Column(JSON, nullable=False, default=dict)
    first_seen_at = Column(DateTime, nullable=False)
    last_seen_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, ForeignKey("console_users.user_id"), nullable=True)
    resolution_note = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now)


class FollowUpContribution(Base):
    __tablename__ = "follow_up_contributions"

    entry_id = Column(String, primary_key=True)  # root finding entry id of a correction chain
    follow_up_id = Column(String, ForeignKey("follow_ups.follow_up_id", ondelete="CASCADE"), nullable=False)
    minutes = Column(Float, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime, nullable=False, default=utc_now)


class FollowUpComment(Base):
    __tablename__ = "follow_up_comments"
    __table_args__ = (CheckConstraint("length(text) BETWEEN 1 AND 1000", name="ck_comments_length"),)

    comment_id = Column(String, primary_key=True, default=_uuid)
    follow_up_id = Column(String, ForeignKey("follow_ups.follow_up_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("console_users.user_id"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            _in("status", ("awaiting_report", "reported", "reviewed")), name="ck_incidents_status"
        ),
        CheckConstraint(_in("origin", ("auto", "operator")), name="ck_incidents_origin"),
        Index("incidents_site_time", "site_id", "occurred_at"),
        Index("incidents_zone", "zone_id", "type", "occurred_at"),
    )

    incident_id = Column(String, primary_key=True, default=_uuid)
    device_id = Column(String, ForeignKey("devices.device_id"), nullable=True)
    machine_id = Column(String, ForeignKey("machines.machine_id"), nullable=False)
    operator_id = Column(String, nullable=True)
    shift_id = Column(String, nullable=True)
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    zone_id = Column(String, nullable=True)
    occurred_at = Column(DateTime, nullable=False)
    type = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    status = Column(String, nullable=False, default="awaiting_report")
    origin = Column(String, nullable=False)
    fields = Column(
        JSON, nullable=False, default=dict
    )  # IncidentFields (§5.3.3): {name: {value, source, entry_id}}
    snapshot = Column(JSON, nullable=True)
    snapshot_complete = Column(Boolean, nullable=False, default=False)
    chain_ok = Column(Boolean, nullable=False, default=True)
    reviewed_by = Column(String, ForeignKey("console_users.user_id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(String, nullable=True)
    sent_to_trainer = Column(Boolean, nullable=False, default=False)
    scenario_id = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now)


class Scenario(Base):
    __tablename__ = "scenarios"
    __table_args__ = (
        CheckConstraint(_in("status", ("draft", "approved", "rejected")), name="ck_scenarios_status"),
        CheckConstraint(_in("draft_method", ("template", "llm")), name="ck_scenarios_method"),
    )

    scenario_id = Column(String, primary_key=True)
    source_incident_id = Column(String, ForeignKey("incidents.incident_id"), nullable=True)
    machine_class = Column(String, nullable=False)
    site_id = Column(String, nullable=True)
    status = Column(String, nullable=False)
    draft_method = Column(String, nullable=False)
    body = Column(JSON, nullable=False)
    prompt_version = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now)
    updated_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_reason = Column(String, nullable=True)
    published_change_seq = Column(Integer, nullable=True)


class HelpRequest(Base):
    __tablename__ = "help_requests"
    __table_args__ = (CheckConstraint(_in("status", ("open", "answered")), name="ck_help_status"),)

    request_id = Column(String, primary_key=True)
    operator_id = Column(String, nullable=False)
    machine_id = Column(String, nullable=False)
    content_id = Column(String, nullable=False)
    question_text = Column(String, nullable=True)
    status = Column(String, nullable=False, default="open")
    answered_by = Column(String, ForeignKey("console_users.user_id"), nullable=True)
    answer_text = Column(String, nullable=True)
    answered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)


class Handover(Base):
    __tablename__ = "handovers"
    __table_args__ = (
        CheckConstraint(_in("wording_method", ("template", "llm")), name="ck_handovers_method"),
    )

    handover_id = Column(String, primary_key=True)
    machine_id = Column(String, ForeignKey("machines.machine_id"), nullable=False)
    from_shift_id = Column(String, nullable=True)
    from_operator_id = Column(String, nullable=True)
    device_id = Column(String, nullable=True)
    voice_note_upload_id = Column(String, nullable=True)
    wording_method = Column(String, nullable=False, default="template")
    created_at = Column(DateTime, nullable=False)
    data_origin = Column(String, nullable=False, default="live")


class HandoverItem(Base):
    __tablename__ = "handover_items"
    __table_args__ = (
        CheckConstraint(
            _in(
                "item_type",
                ("unfinished_task", "blocked_task", "defect", "incident", "site_delay", "note", "tip"),
            ),
            name="ck_handover_items_type",
        ),
        CheckConstraint(_in("status", ("open", "resolved", "removed")), name="ck_handover_items_status"),
        Index("handover_items_open", "status"),
    )

    item_id = Column(String, primary_key=True)
    handover_id = Column(String, ForeignKey("handovers.handover_id", ondelete="CASCADE"), nullable=False)
    item_type = Column(String, nullable=False)
    text = Column(String, nullable=False)
    audiences = Column(JSON, nullable=False)
    source_entry_ids = Column(JSON, nullable=False, default=list)
    task_id = Column(String, nullable=True)
    incident_id = Column(String, nullable=True)
    follow_up_id = Column(String, nullable=True)
    carried_from_item_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="open")
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)  # console user_id, or 'task_completed'
    resolved_at = Column(DateTime, nullable=True)
    resolution_note = Column(String, nullable=True)


class ChangeLog(Base):
    __tablename__ = "change_log"
    __table_args__ = (
        CheckConstraint(
            _in("scope_type", ("machine", "site", "machine_class", "all")), name="ck_change_log_scope"
        ),
        Index("change_log_scope", "scope_type", "scope_id", "seq"),
    )

    seq = Column(Integer, primary_key=True, autoincrement=True)
    scope_type = Column(String, nullable=False)
    scope_id = Column(String, nullable=True)  # NULL for scope 'all'
    change_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class Upload(Base):
    __tablename__ = "uploads"
    __table_args__ = (
        CheckConstraint(_in("kind", ("voice_note", "site_tip")), name="ck_uploads_kind"),
        CheckConstraint(_in("content_type", ("audio/mp4", "audio/webm")), name="ck_uploads_type"),
        CheckConstraint("size_bytes BETWEEN 1 AND 1048576", name="ck_uploads_size"),
    )

    upload_id = Column(String, primary_key=True, default=_uuid)
    entry_id = Column(String, nullable=False, unique=True)
    device_id = Column(String, ForeignKey("devices.device_id"), nullable=False)
    kind = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    storage_key = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class SosEvent(Base):
    __tablename__ = "sos_events"
    __table_args__ = (
        CheckConstraint(_in("event_type", ("sos", "cancel")), name="ck_sos_event_type"),
        CheckConstraint(_in("received_via", ("lora_sim", "https")), name="ck_sos_via"),
        UniqueConstraint("machine_id", "seq", name="uq_sos_machine_seq"),
    )

    sos_id = Column(String, primary_key=True, default=_uuid)
    machine_id = Column(String, ForeignKey("machines.machine_id"), nullable=False)
    seq = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    device_time = Column(DateTime, nullable=False)
    severity = Column(Integer, nullable=False)
    received_via = Column(String, nullable=False)
    gateway_id = Column(String, nullable=True)
    rssi = Column(Integer, nullable=True)
    snr = Column(Float, nullable=True)
    received_at = Column(DateTime, nullable=False, default=utc_now)
    acknowledged_by = Column(String, ForeignKey("console_users.user_id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    response_note = Column(String, nullable=True)


class SmsOutbox(Base):
    __tablename__ = "sms_outbox"

    sms_id = Column(String, primary_key=True, default=_uuid)
    sos_id = Column(String, ForeignKey("sos_events.sos_id"), nullable=False)
    to_masked = Column(String, nullable=False)
    body = Column(String, nullable=False)
    status = Column(String, nullable=False, default="simulated")
    created_at = Column(DateTime, nullable=False, default=utc_now)


class ModelArtifact(Base):
    __tablename__ = "model_artifacts"
    __table_args__ = (CheckConstraint(_in("kind", ("estimator", "intent")), name="ck_model_artifacts_kind"),)

    artifact_id = Column(String, primary_key=True)
    kind = Column(String, nullable=False)
    machine_class = Column(String, nullable=True)
    version = Column(Integer, nullable=False)
    body = Column(JSON, nullable=False)
    published_at = Column(DateTime, nullable=False, default=utc_now)


class Forecast(Base):
    __tablename__ = "forecasts"
    __table_args__ = (
        CheckConstraint(_in("source", ("open_meteo", "seed")), name="ck_forecasts_source"),
        CheckConstraint("visibility_m IS NULL OR visibility_m >= 0", name="ck_forecasts_visibility"),
    )

    site_id = Column(String, ForeignKey("sites.site_id"), primary_key=True)
    valid_from = Column(DateTime, primary_key=True)
    valid_to = Column(DateTime, nullable=False)
    weather = Column(String, nullable=False)
    visibility = Column(String, nullable=False)
    visibility_m = Column(Float, nullable=True)
    temp_c = Column(Float, nullable=False)
    heat_index_c = Column(Float, nullable=True)
    wind_kmh = Column(Float, nullable=False)
    precipitation_mm = Column(Float, nullable=False)
    issued_at = Column(DateTime, nullable=False)
    source = Column(String, nullable=False, default="seed")


class FleetStatus(Base):
    __tablename__ = "fleet_status"

    machine_id = Column(String, ForeignKey("machines.machine_id"), primary_key=True)
    state = Column(String, nullable=False)
    open_alerts = Column(Integer, nullable=False, default=0)
    last_sync_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=utc_now)
    data_origin = Column(String, nullable=False, default="synthetic")


class MachineSummary(Base):
    __tablename__ = "machine_summaries"

    entry_id = Column(String, ForeignKey("ledger_entries.entry_id"), primary_key=True)
    machine_id = Column(String, nullable=False)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    metrics = Column(JSON, nullable=False)
    iso_score = Column(Float, nullable=True)
    iso_flag = Column(Boolean, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String, nullable=False)  # console user_id | 'device:<id>' | 'cli'
    action = Column(String, nullable=False)
    target_type = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    detail = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=utc_now)
