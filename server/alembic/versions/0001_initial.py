"""Initial schema (technical spec §5.2; task T20).

Explicit DDL mirroring shiftmate/models.py: every column, CHECK constraint, foreign key and (partial) unique
index. Runs on SQLite (local development) and PostgreSQL 16 (site server). Never edit after it has been applied;
add a new revision instead (§10.5).

Revision ID: 0001
Revises:
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("audit_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.String(), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("audit_id"),
    )
    op.create_table(
        "change_log",
        sa.Column("seq", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scope_type", sa.String(), nullable=False),
        sa.Column("scope_id", sa.String(), nullable=True),
        sa.Column("change_type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "scope_type IN ('machine', 'site', 'machine_class', 'all')", name="ck_change_log_scope"
        ),
        sa.PrimaryKeyConstraint("seq"),
    )
    op.create_index("change_log_scope", "change_log", ["scope_type", "scope_id", "seq"], unique=False)

    op.create_table(
        "console_users",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("site_ids", sa.JSON(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("disabled_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "role IN ('supervisor', 'trainer', 'safety', 'mechanic')", name="ck_console_users_role"
        ),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "machine_profiles",
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("machine_class", sa.String(), nullable=False),
        sa.Column("body", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("profile_id", "version"),
    )
    op.create_table(
        "model_artifacts",
        sa.Column("artifact_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("machine_class", sa.String(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("body", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("kind IN ('estimator', 'intent')", name="ck_model_artifacts_kind"),
        sa.PrimaryKeyConstraint("artifact_id"),
    )
    op.create_table(
        "sites",
        sa.Column("site_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sector", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("utc_offset_minutes", sa.Integer(), nullable=False),
        sa.Column("diesel_price_inr_per_l", sa.Float(), nullable=False),
        sa.Column("dark_start_local", sa.String(), nullable=False),
        sa.Column("dark_end_local", sa.String(), nullable=False),
        sa.Column("job_efficiency_override", sa.Float(), nullable=True),
        sa.Column("congestion_level", sa.String(), nullable=False),
        sa.Column("data_origin", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("congestion_level IN ('low', 'medium', 'high')", name="ck_sites_congestion"),
        sa.CheckConstraint("sector IN ('construction', 'mining')", name="ck_sites_sector"),
        sa.CheckConstraint(
            "job_efficiency_override IS NULL OR (job_efficiency_override > 0 AND job_efficiency_override <= 1)",
            name="ck_sites_job_efficiency",
        ),
        sa.PrimaryKeyConstraint("site_id"),
    )
    op.create_table(
        "console_sessions",
        sa.Column("session_id", sa.String(length=43), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["console_users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_table(
        "follow_ups",
        sa.Column("follow_up_id", sa.String(), nullable=False),
        sa.Column("site_id", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("group_key", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("assigned_to", sa.String(), nullable=True),
        sa.Column("machine_id", sa.String(), nullable=True),
        sa.Column("zone_id", sa.String(), nullable=True),
        sa.Column("reason_code", sa.String(), nullable=True),
        sa.Column("related_id", sa.String(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.String(), nullable=True),
        sa.Column("resolution_note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "category IN ('site_delay', 'machine_check', 'safety_incident', 'help_request', 'assignment_request', 'supervisor_notification', 'sync_conflict', 'near_miss_cluster', 'overspeed_zone', 'alert_review', 'usage_review', 'sos', 'chain_integrity')",
            name="ck_follow_ups_category",
        ),
        sa.CheckConstraint("status IN ('open', 'assigned', 'resolved')", name="ck_follow_ups_status"),
        sa.CheckConstraint("priority BETWEEN 0 AND 3", name="ck_follow_ups_priority"),
        sa.ForeignKeyConstraint(
            ["assigned_to"],
            ["console_users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by"],
            ["console_users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.site_id"],
        ),
        sa.PrimaryKeyConstraint("follow_up_id"),
    )
    op.create_index(
        "follow_ups_list", "follow_ups", ["site_id", "status", "priority", "first_seen_at"], unique=False
    )
    op.create_index(
        "follow_ups_open_group",
        "follow_ups",
        ["group_key"],
        unique=True,
        sqlite_where=sa.text("status <> 'resolved'"),
        postgresql_where=sa.text("status <> 'resolved'"),
    )

    op.create_table(
        "forecasts",
        sa.Column("site_id", sa.String(), nullable=False),
        sa.Column("valid_from", sa.DateTime(), nullable=False),
        sa.Column("valid_to", sa.DateTime(), nullable=False),
        sa.Column("weather", sa.String(), nullable=False),
        sa.Column("visibility", sa.String(), nullable=False),
        sa.Column("visibility_m", sa.Float(), nullable=True),
        sa.Column("temp_c", sa.Float(), nullable=False),
        sa.Column("heat_index_c", sa.Float(), nullable=True),
        sa.Column("wind_kmh", sa.Float(), nullable=False),
        sa.Column("precipitation_mm", sa.Float(), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.CheckConstraint("source IN ('open_meteo', 'seed')", name="ck_forecasts_source"),
        sa.CheckConstraint("visibility_m IS NULL OR visibility_m >= 0", name="ck_forecasts_visibility"),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.site_id"],
        ),
        sa.PrimaryKeyConstraint("site_id", "valid_from"),
    )
    op.create_table(
        "help_requests",
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("operator_id", sa.String(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("content_id", sa.String(), nullable=False),
        sa.Column("question_text", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("answered_by", sa.String(), nullable=True),
        sa.Column("answer_text", sa.String(), nullable=True),
        sa.Column("answered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('open', 'answered')", name="ck_help_status"),
        sa.ForeignKeyConstraint(
            ["answered_by"],
            ["console_users.user_id"],
        ),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_table(
        "machines",
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("short_id", sa.Integer(), nullable=False),
        sa.Column("site_id", sa.String(), nullable=False),
        sa.Column("profile_id", sa.String(), nullable=False),
        sa.Column("profile_version", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=False),
        sa.Column("year_of_manufacture", sa.Integer(), nullable=False),
        sa.Column("detail_level", sa.String(), nullable=False),
        sa.Column("data_origin", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("detail_level IN ('detailed', 'status_only')", name="ck_machines_detail"),
        sa.CheckConstraint("short_id BETWEEN 1 AND 65535", name="ck_machines_short_id"),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.site_id"],
        ),
        sa.PrimaryKeyConstraint("machine_id"),
        sa.UniqueConstraint("short_id"),
    )
    op.create_table(
        "operators",
        sa.Column("operator_id", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("skill_level", sa.String(), nullable=False),
        sa.Column("experience_months", sa.Integer(), nullable=False),
        sa.Column("hired_at", sa.Date(), nullable=False),
        sa.Column("site_id", sa.String(), nullable=False),
        sa.Column("pin_salt", sa.String(length=32), nullable=False),
        sa.Column("pin_hash", sa.String(length=64), nullable=False),
        sa.Column("pin_iterations", sa.Integer(), nullable=False),
        sa.Column("data_origin", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("language IN ('en', 'hi', 'ta')", name="ck_operators_language"),
        sa.CheckConstraint(
            "skill_level IN ('beginner', 'intermediate', 'expert')", name="ck_operators_skill"
        ),
        sa.CheckConstraint("experience_months >= 0", name="ck_operators_experience"),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.site_id"],
        ),
        sa.PrimaryKeyConstraint("operator_id"),
    )
    op.create_table(
        "zones",
        sa.Column("zone_id", sa.String(), nullable=False),
        sa.Column("site_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("center_lat", sa.Float(), nullable=False),
        sa.Column("center_lon", sa.Float(), nullable=False),
        sa.Column("radius_m", sa.Float(), nullable=False),
        sa.Column("speed_limit_kmh", sa.Float(), nullable=True),
        sa.CheckConstraint(
            "kind IN ('trench_area', 'loading_bay', 'yard', 'haul_road', 'shovel', 'crusher', 'dump', 'other')",
            name="ck_zones_kind",
        ),
        sa.CheckConstraint("radius_m > 0", name="ck_zones_radius"),
        sa.ForeignKeyConstraint(["site_id"], ["sites.site_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("zone_id"),
    )
    op.create_index("zones_site", "zones", ["site_id"], unique=False)

    op.create_table(
        "devices",
        sa.Column("device_id", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("paired_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("last_push_at", sa.DateTime(), nullable=True),
        sa.Column("last_pull_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["machine_id"],
            ["machines.machine_id"],
        ),
        sa.PrimaryKeyConstraint("device_id"),
    )
    op.create_table(
        "fleet_status",
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("open_alerts", sa.Integer(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("data_origin", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["machine_id"],
            ["machines.machine_id"],
        ),
        sa.PrimaryKeyConstraint("machine_id"),
    )
    op.create_table(
        "follow_up_comments",
        sa.Column("comment_id", sa.String(), nullable=False),
        sa.Column("follow_up_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("length(text) BETWEEN 1 AND 1000", name="ck_comments_length"),
        sa.ForeignKeyConstraint(["follow_up_id"], ["follow_ups.follow_up_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["console_users.user_id"],
        ),
        sa.PrimaryKeyConstraint("comment_id"),
    )
    op.create_table(
        "follow_up_contributions",
        sa.Column("entry_id", sa.String(), nullable=False),
        sa.Column("follow_up_id", sa.String(), nullable=False),
        sa.Column("minutes", sa.Float(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["follow_up_id"], ["follow_ups.follow_up_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("entry_id"),
    )
    op.create_table(
        "handovers",
        sa.Column("handover_id", sa.String(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("from_shift_id", sa.String(), nullable=True),
        sa.Column("from_operator_id", sa.String(), nullable=True),
        sa.Column("device_id", sa.String(), nullable=True),
        sa.Column("voice_note_upload_id", sa.String(), nullable=True),
        sa.Column("wording_method", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("data_origin", sa.String(), nullable=False),
        sa.CheckConstraint("wording_method IN ('template', 'llm')", name="ck_handovers_method"),
        sa.ForeignKeyConstraint(
            ["machine_id"],
            ["machines.machine_id"],
        ),
        sa.PrimaryKeyConstraint("handover_id"),
    )
    op.create_table(
        "pairing_codes",
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("reusable", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("used_by_device_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["machine_id"],
            ["machines.machine_id"],
        ),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "sos_events",
        sa.Column("sos_id", sa.String(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("device_time", sa.DateTime(), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("received_via", sa.String(), nullable=False),
        sa.Column("gateway_id", sa.String(), nullable=True),
        sa.Column("rssi", sa.Integer(), nullable=True),
        sa.Column("snr", sa.Float(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("acknowledged_by", sa.String(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("response_note", sa.String(), nullable=True),
        sa.CheckConstraint("event_type IN ('sos', 'cancel')", name="ck_sos_event_type"),
        sa.CheckConstraint("received_via IN ('lora_sim', 'https')", name="ck_sos_via"),
        sa.ForeignKeyConstraint(
            ["acknowledged_by"],
            ["console_users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["machine_id"],
            ["machines.machine_id"],
        ),
        sa.PrimaryKeyConstraint("sos_id"),
        sa.UniqueConstraint("machine_id", "seq", name="uq_sos_machine_seq"),
    )
    op.create_table(
        "task_assignments",
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("site_id", sa.String(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=True),
        sa.Column("task_type", sa.String(), nullable=False),
        sa.Column("zone_id", sa.String(), nullable=True),
        sa.Column("location_text", sa.String(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("material", sa.String(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("completion_criterion", sa.String(), nullable=False),
        sa.Column("planner_minutes", sa.Float(), nullable=True),
        sa.Column("planned_date", sa.Date(), nullable=False),
        sa.Column("planned_start_at", sa.DateTime(), nullable=True),
        sa.Column("planned_start_window_min", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("exec_state", sa.String(), nullable=False),
        sa.Column("exec_updated_at", sa.DateTime(), nullable=True),
        sa.Column("actual_start", sa.DateTime(), nullable=True),
        sa.Column("actual_end", sa.DateTime(), nullable=True),
        sa.Column("active_min", sa.Float(), nullable=True),
        sa.Column("waiting_min", sa.Float(), nullable=True),
        sa.Column("output_qty", sa.Float(), nullable=True),
        sa.Column("data_origin", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "exec_state IN ('PLANNED', 'ACTIVE', 'PAUSED', 'BLOCKED', 'COMPLETED', 'CANCELLED')",
            name="ck_tasks_exec_state",
        ),
        sa.CheckConstraint("source IN ('dispatcher', 'seed', 'reassignment')", name="ck_tasks_source"),
        sa.CheckConstraint("status IN ('assigned', 'cancelled')", name="ck_tasks_status"),
        sa.CheckConstraint("unit IN ('m', 'm2', 'm3', 't', 'loads', 'lifts')", name="ck_tasks_unit"),
        sa.CheckConstraint("planned_start_window_min BETWEEN 0 AND 240", name="ck_tasks_window"),
        sa.CheckConstraint("priority BETWEEN 1 AND 3", name="ck_tasks_priority"),
        sa.CheckConstraint("quantity > 0", name="ck_tasks_quantity"),
        sa.ForeignKeyConstraint(
            ["machine_id"],
            ["machines.machine_id"],
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.site_id"],
        ),
        sa.ForeignKeyConstraint(
            ["zone_id"],
            ["zones.zone_id"],
        ),
        sa.PrimaryKeyConstraint("task_id"),
    )
    op.create_index("tasks_machine_date", "task_assignments", ["machine_id", "planned_date"], unique=False)

    op.create_table(
        "handover_items",
        sa.Column("item_id", sa.String(), nullable=False),
        sa.Column("handover_id", sa.String(), nullable=False),
        sa.Column("item_type", sa.String(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("audiences", sa.JSON(), nullable=False),
        sa.Column("source_entry_ids", sa.JSON(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.Column("incident_id", sa.String(), nullable=True),
        sa.Column("follow_up_id", sa.String(), nullable=True),
        sa.Column("carried_from_item_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("acknowledged_by", sa.String(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.String(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolution_note", sa.String(), nullable=True),
        sa.CheckConstraint(
            "item_type IN ('unfinished_task', 'blocked_task', 'defect', 'incident', 'site_delay', 'note', 'tip')",
            name="ck_handover_items_type",
        ),
        sa.CheckConstraint("status IN ('open', 'resolved', 'removed')", name="ck_handover_items_status"),
        sa.ForeignKeyConstraint(["handover_id"], ["handovers.handover_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("item_id"),
    )
    op.create_index("handover_items_open", "handover_items", ["status"], unique=False)

    op.create_table(
        "incidents",
        sa.Column("incident_id", sa.String(), nullable=False),
        sa.Column("device_id", sa.String(), nullable=True),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("operator_id", sa.String(), nullable=True),
        sa.Column("shift_id", sa.String(), nullable=True),
        sa.Column("site_id", sa.String(), nullable=False),
        sa.Column("zone_id", sa.String(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("severity", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("origin", sa.String(), nullable=False),
        sa.Column("fields", sa.JSON(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=True),
        sa.Column("snapshot_complete", sa.Boolean(), nullable=False),
        sa.Column("chain_ok", sa.Boolean(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_note", sa.String(), nullable=True),
        sa.Column("sent_to_trainer", sa.Boolean(), nullable=False),
        sa.Column("scenario_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("origin IN ('auto', 'operator')", name="ck_incidents_origin"),
        sa.CheckConstraint(
            "status IN ('awaiting_report', 'reported', 'reviewed')", name="ck_incidents_status"
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.device_id"],
        ),
        sa.ForeignKeyConstraint(
            ["machine_id"],
            ["machines.machine_id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["console_users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.site_id"],
        ),
        sa.PrimaryKeyConstraint("incident_id"),
    )
    op.create_index("incidents_site_time", "incidents", ["site_id", "occurred_at"], unique=False)
    op.create_index("incidents_zone", "incidents", ["zone_id", "type", "occurred_at"], unique=False)

    op.create_table(
        "ledger_entries",
        sa.Column("entry_id", sa.String(), nullable=False),
        sa.Column("device_id", sa.String(), nullable=True),
        sa.Column("author_user_id", sa.String(), nullable=True),
        sa.Column("shift_id", sa.String(), nullable=True),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("operator_id", sa.String(), nullable=True),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("subtype", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("freshness_s", sa.Float(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=True),
        sa.Column("rule_or_model_version", sa.String(), nullable=True),
        sa.Column("original_text", sa.String(), nullable=True),
        sa.Column("supersedes", sa.String(), nullable=True),
        sa.Column("audience", sa.String(), nullable=False),
        sa.Column("data_origin", sa.String(), nullable=False),
        sa.Column("payload_sha256", sa.String(length=64), nullable=False),
        sa.Column("chain_seq", sa.Integer(), nullable=True),
        sa.Column("prev_hash", sa.String(length=64), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("canonical_payload", sa.String(), nullable=True),
        sa.Column("review_status", sa.String(), nullable=False),
        sa.Column("review_reason", sa.String(), nullable=True),
        sa.CheckConstraint(
            "audience IN ('next_operator', 'site', 'trainer', 'safety')", name="ck_ledger_audience"
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR confidence IN ('high', 'medium', 'low')", name="ck_ledger_confidence"
        ),
        sa.CheckConstraint("review_status IN ('ok', 'needs_review')", name="ck_ledger_review"),
        sa.CheckConstraint(
            "source IN ('observed', 'reported', 'inferred', 'reviewed')", name="ck_ledger_source"
        ),
        sa.ForeignKeyConstraint(
            ["author_user_id"],
            ["console_users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.device_id"],
        ),
        sa.PrimaryKeyConstraint("entry_id"),
    )
    op.create_index(
        "ledger_chain",
        "ledger_entries",
        ["device_id", "chain_seq"],
        unique=True,
        sqlite_where=sa.text("chain_seq IS NOT NULL"),
        postgresql_where=sa.text("chain_seq IS NOT NULL"),
    )
    op.create_index("ledger_kind", "ledger_entries", ["kind", "subtype"], unique=False)
    op.create_index("ledger_machine_time", "ledger_entries", ["machine_id", "observed_at"], unique=False)
    op.create_index("ledger_supersedes", "ledger_entries", ["supersedes"], unique=False)

    op.create_table(
        "reassignment_requests",
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("operator_id", sa.String(), nullable=False),
        sa.Column("reason_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("decided_by", sa.String(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("new_machine_id", sa.String(), nullable=True),
        sa.Column("decision_note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'accepted', 'rejected')", name="ck_reassign_status"),
        sa.ForeignKeyConstraint(
            ["decided_by"],
            ["console_users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task_assignments.task_id"],
        ),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_table(
        "shifts",
        sa.Column("shift_id", sa.String(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("operator_id", sa.String(), nullable=False),
        sa.Column("device_id", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.device_id"],
        ),
        sa.ForeignKeyConstraint(
            ["machine_id"],
            ["machines.machine_id"],
        ),
        sa.ForeignKeyConstraint(
            ["operator_id"],
            ["operators.operator_id"],
        ),
        sa.PrimaryKeyConstraint("shift_id"),
    )
    op.create_table(
        "sms_outbox",
        sa.Column("sms_id", sa.String(), nullable=False),
        sa.Column("sos_id", sa.String(), nullable=False),
        sa.Column("to_masked", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["sos_id"],
            ["sos_events.sos_id"],
        ),
        sa.PrimaryKeyConstraint("sms_id"),
    )
    op.create_table(
        "uploads",
        sa.Column("upload_id", sa.String(), nullable=False),
        sa.Column("entry_id", sa.String(), nullable=False),
        sa.Column("device_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("content_type IN ('audio/mp4', 'audio/webm')", name="ck_uploads_type"),
        sa.CheckConstraint("kind IN ('voice_note', 'site_tip')", name="ck_uploads_kind"),
        sa.CheckConstraint("size_bytes BETWEEN 1 AND 1048576", name="ck_uploads_size"),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.device_id"],
        ),
        sa.PrimaryKeyConstraint("upload_id"),
        sa.UniqueConstraint("entry_id"),
    )
    op.create_table(
        "machine_summaries",
        sa.Column("entry_id", sa.String(), nullable=False),
        sa.Column("machine_id", sa.String(), nullable=False),
        sa.Column("window_start", sa.DateTime(), nullable=False),
        sa.Column("window_end", sa.DateTime(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("iso_score", sa.Float(), nullable=True),
        sa.Column("iso_flag", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["entry_id"],
            ["ledger_entries.entry_id"],
        ),
        sa.PrimaryKeyConstraint("entry_id"),
    )
    op.create_table(
        "scenarios",
        sa.Column("scenario_id", sa.String(), nullable=False),
        sa.Column("source_incident_id", sa.String(), nullable=True),
        sa.Column("machine_class", sa.String(), nullable=False),
        sa.Column("site_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("draft_method", sa.String(), nullable=False),
        sa.Column("body", sa.JSON(), nullable=False),
        sa.Column("prompt_version", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column("approved_by", sa.String(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_reason", sa.String(), nullable=True),
        sa.Column("published_change_seq", sa.Integer(), nullable=True),
        sa.CheckConstraint("draft_method IN ('template', 'llm')", name="ck_scenarios_method"),
        sa.CheckConstraint("status IN ('draft', 'approved', 'rejected')", name="ck_scenarios_status"),
        sa.ForeignKeyConstraint(
            ["source_incident_id"],
            ["incidents.incident_id"],
        ),
        sa.PrimaryKeyConstraint("scenario_id"),
    )


def downgrade() -> None:
    # Reverse creation order; indexes go with their tables.
    op.drop_table("scenarios")
    op.drop_table("machine_summaries")
    op.drop_table("uploads")
    op.drop_table("sms_outbox")
    op.drop_table("shifts")
    op.drop_table("reassignment_requests")
    op.drop_table("ledger_entries")
    op.drop_table("incidents")
    op.drop_table("handover_items")
    op.drop_table("task_assignments")
    op.drop_table("sos_events")
    op.drop_table("pairing_codes")
    op.drop_table("handovers")
    op.drop_table("follow_up_contributions")
    op.drop_table("follow_up_comments")
    op.drop_table("fleet_status")
    op.drop_table("devices")
    op.drop_table("zones")
    op.drop_table("operators")
    op.drop_table("machines")
    op.drop_table("help_requests")
    op.drop_table("forecasts")
    op.drop_table("follow_ups")
    op.drop_table("console_sessions")
    op.drop_table("sites")
    op.drop_table("model_artifacts")
    op.drop_table("machine_profiles")
    op.drop_table("console_users")
    op.drop_table("change_log")
    op.drop_table("audit_log")
