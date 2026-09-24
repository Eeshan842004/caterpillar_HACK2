"""Push handling and server projections (technical spec §5.5, §6.2 push rules, §8.21).

Each pushed envelope is validated, stored idempotently and projected inside its own SAVEPOINT, so one bad
entry is rejected on its own without failing the rest of the batch.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from shiftmate.models import (
    Device,
    FollowUp,
    Handover,
    HandoverItem,
    HelpRequest,
    Incident,
    LedgerEntry,
    Machine,
    MachineSummary,
    ReassignmentRequest,
    Shift,
    Site,
    TaskAssignment,
    Zone,
)
from shiftmate.schemas.ledger import SERVER_ONLY, VERSIONED_KINDS, PayloadError, validate_ledger_payload
from shiftmate.schemas.sync import OutboxEnvelope, SyncPushResult
from shiftmate.services.chain import first_bad_chain_seq
from shiftmate.services.changes import record_change
from shiftmate.services.followups import open_group, set_site_delay_contribution
from shiftmate.services.machine_context import MachineContext, machine_context
from shiftmate.time_util import utc_now

log = logging.getLogger("shiftmate.projection")

SOURCE_RANK = {"observed": 1, "inferred": 2, "reported": 3, "reviewed": 4}
INCIDENT_FAMILY = {("report", "incident_report"), ("inference", "incident_extraction")}


class Rejected(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def parse_ts(value: str | None) -> datetime:
    """Strict ISO-8601 UTC parse. Raises Rejected instead of silently substituting 'now' (audit item 7)."""
    if not value or not isinstance(value, str) or not value.endswith("Z"):
        raise Rejected("invalid_timestamp")
    try:
        return datetime.fromisoformat(value[:-1])
    except ValueError as exc:
        raise Rejected("invalid_timestamp") from exc


def wire_sha256(entry: dict[str, Any]) -> str:
    """Idempotency hash over the whole wire entry (§5.5), independent of JS number formatting."""
    return hashlib.sha256(
        json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def local_date(ctx: MachineContext, at: datetime) -> str:
    return (at + timedelta(minutes=ctx.utc_offset_minutes)).strftime("%Y-%m-%d")


# ----------------------------------------------------------------------------------------------- push


def project_envelope(db: Session, device: Device, envelope: OutboxEnvelope) -> SyncPushResult:
    ctx = machine_context(db, device.machine_id)
    try:
        with db.begin_nested():
            status, reason = _handle(db, device, ctx, envelope)
        return SyncPushResult(entry_id=envelope.entry_id, status=status, reason=reason)
    except Rejected as exc:
        return SyncPushResult(entry_id=envelope.entry_id, status="rejected", reason=exc.reason)
    except Exception:
        log.exception("projection_error entry_id=%s", envelope.entry_id)
        return SyncPushResult(entry_id=envelope.entry_id, status="rejected", reason="projection_error")


def _handle(db: Session, device: Device, ctx: MachineContext, env: OutboxEnvelope) -> tuple[str, str | None]:
    body = env.body
    if body.kind == "handover_bundle":
        return _handover_bundle(db, device, ctx, env)
    if body.kind != "ledger_entry" or body.entry is None:
        raise Rejected("missing_entry")

    wire = body.entry.model_dump(mode="json")
    entry = body.entry
    kind, subtype = entry.kind.value, entry.subtype
    if entry.entry_id != env.entry_id:
        raise Rejected("entry_id_mismatch")

    digest = wire_sha256(wire)
    existing = db.get(LedgerEntry, entry.entry_id)
    if existing is not None:
        if existing.payload_sha256 == digest:
            return "duplicate", None
        raise Rejected("id_reuse_different_payload")

    if entry.audience.value == "operator_only" or kind == "learning_event":
        raise Rejected("private_not_accepted")
    if entry.machine_id != device.machine_id:
        raise Rejected("machine_mismatch")
    if (kind, subtype) in SERVER_ONLY:
        raise Rejected("server_only_subtype")
    if entry.device_id is not None and entry.device_id != device.device_id:
        raise Rejected("device_mismatch")
    try:
        validate_ledger_payload(kind, subtype, entry.payload)
    except PayloadError as exc:
        raise Rejected(f"validation_error: {exc}") from exc
    if kind in VERSIONED_KINDS and not entry.rule_or_model_version:
        raise Rejected("missing_rule_version")
    observed_at, recorded_at = parse_ts(entry.observed_at), parse_ts(entry.recorded_at)

    row = LedgerEntry(
        entry_id=entry.entry_id, device_id=device.device_id, shift_id=entry.shift_id, machine_id=entry.machine_id,
        operator_id=entry.operator_id, kind=kind, subtype=subtype, source=entry.source.value, payload=entry.payload,
        observed_at=observed_at, recorded_at=recorded_at, received_at=utc_now(), freshness_s=entry.freshness_s,
        confidence=entry.confidence, rule_or_model_version=entry.rule_or_model_version,
        original_text=entry.original_text, supersedes=entry.supersedes, audience=entry.audience.value,
        data_origin=entry.data_origin, payload_sha256=digest, chain_seq=entry.chain_seq, prev_hash=entry.prev_hash,
        content_hash=entry.content_hash, canonical_payload=entry.canonical_payload, review_status="ok",
    )
    db.add(row)
    db.flush()
    return _project(db, device, ctx, row)


# ----------------------------------------------------------------------------------------------- projectors


def _project(db: Session, device: Device, ctx: MachineContext, row: LedgerEntry) -> tuple[str, str | None]:
    kind, subtype, p = row.kind, row.subtype, row.payload

    if kind == "shift_event":
        if subtype == "start":
            db.merge(Shift(shift_id=row.shift_id or row.entry_id, machine_id=row.machine_id,
                           operator_id=row.operator_id, device_id=device.device_id, started_at=row.observed_at))
        elif row.shift_id:
            shift = db.get(Shift, row.shift_id)
            if shift:
                shift.ended_at = row.observed_at
        return "confirmed", None

    if kind == "task_event":
        return _task_event(db, ctx, row)

    if (kind == "inference" and subtype == "finding") or (kind == "correction" and subtype == "finding"):
        _finding(db, ctx, row)
        return "confirmed", None

    if kind == "incident" or (kind, subtype) in INCIDENT_FAMILY or (
        kind == "correction" and subtype in {"incident_report", "incident_extraction"}
    ):
        _incident(db, device, ctx, row)
        return "confirmed", None

    if kind == "alert" and subtype == "raised" and p.get("alert_type") == "A-SPEED" and p.get("zone_id"):
        _overspeed_zone(db, ctx, row)
        return "confirmed", None

    if kind == "observation" and subtype == "signal_summary_5m":
        db.merge(MachineSummary(
            entry_id=row.entry_id, machine_id=row.machine_id,
            window_start=datetime.utcfromtimestamp(p["window_start"] / 1000.0),
            window_end=datetime.utcfromtimestamp(p["window_end"] / 1000.0), metrics=p,
        ))
        return "confirmed", None

    if kind == "report":
        return _report(db, ctx, row)

    if kind == "handover_item" and subtype in {"acknowledged", "resolved"}:
        item = db.get(HandoverItem, p["item_id"])
        if item is not None:
            if subtype == "acknowledged":
                item.acknowledged_by = row.operator_id
                item.acknowledged_at = row.observed_at
                record_change(db, "handover_item.acknowledged", "machine", row.machine_id,
                              {"item_id": item.item_id, "operator_id": row.operator_id,
                               "acknowledged_at": _iso(row.observed_at)})
            else:
                item.status = "resolved"
                item.resolved_by = "task_completed"
                item.resolved_at = row.observed_at
                record_change(db, "handover_item.resolved", "machine", row.machine_id,
                              {"item_id": item.item_id, "resolved_by_role": "task_completed",
                               "resolved_at": _iso(row.observed_at), "note": None})
        return "confirmed", None

    return "confirmed", None       # everything else: mirror only (§8.21)


def _task_event(db: Session, ctx: MachineContext, row: LedgerEntry) -> tuple[str, str | None]:
    p = row.payload
    task = db.get(TaskAssignment, p["task_id"])
    if task is None:
        return "confirmed", None
    moved = task.status == "cancelled" or (task.machine_id is not None and task.machine_id != row.machine_id)
    if moved and p["assignment_revision"] < task.revision:
        reason = "task_cancelled" if task.status == "cancelled" else "assignment_changed"
        row.review_status = "needs_review"
        row.review_reason = reason
        open_group(db, site_id=ctx.site_id, category="sync_conflict", group_key=f"sync_conflict:{row.entry_id}",
                   title=f"Sync conflict on {task.task_id}",
                   summary=f"Operator recorded '{row.subtype}' after the task was {reason.replace('_', ' ')}.",
                   priority=2, at=row.observed_at, machine_id=row.machine_id, related_id=row.entry_id)
        return "needs_review", reason

    state = {"start": "ACTIVE", "resume": "ACTIVE", "pause": "PAUSED", "block": "BLOCKED",
             "complete": "COMPLETED", "cancel": "CANCELLED"}[row.subtype]
    task.exec_state = state
    task.exec_updated_at = row.observed_at
    task.updated_at = utc_now()
    if row.subtype == "start" and task.actual_start is None:
        task.actual_start = row.observed_at
    if row.subtype == "complete":
        task.actual_start = parse_ts(p["actual_start"]) if p.get("actual_start") else task.actual_start
        task.actual_end = parse_ts(p["actual_end"]) if p.get("actual_end") else row.observed_at
        task.active_min = p.get("active_min")
        task.waiting_min = p.get("waiting_min")
        task.output_qty = p.get("output_qty")
    return "confirmed", None


def _root_entry_id(db: Session, row: LedgerEntry) -> str:
    """Root of a correction chain: follow `supersedes` back to the original entry."""
    current, seen = row, set()
    while current.supersedes and current.supersedes not in seen:
        seen.add(current.supersedes)
        parent = db.get(LedgerEntry, current.supersedes)
        if parent is None:
            return current.supersedes           # target not arrived yet; it will reuse the same key
        current = parent
    return current.entry_id


def _finding(db: Session, ctx: MachineContext, row: LedgerEntry) -> None:
    finding = row.payload if row.kind == "inference" else row.payload.get("replacement")
    root = _root_entry_id(db, row) if row.kind == "correction" else row.entry_id
    source = finding or (db.get(LedgerEntry, root).payload if db.get(LedgerEntry, root) else {})
    zone_name = _zone_name(db, source.get("zone_id")) if source else None
    owner = (finding or {}).get("owner")
    if finding is None or owner == "site":
        set_site_delay_contribution(db, root_entry_id=root, finding=finding, at=row.observed_at, zone_name=zone_name)
        return
    pattern = finding["pattern_code"]
    if owner == "machine":
        open_group(db, site_id=ctx.site_id, category="machine_check",
                   group_key=f"machine_check:{row.machine_id}:{pattern}",
                   title=f"Machine check: {pattern.replace('_', ' ')} on {row.machine_id}",
                   summary=", ".join(finding.get("possible_explanations", [])) or pattern,
                   priority=2, at=row.observed_at, machine_id=row.machine_id, related_id=root)
    elif owner == "needs_review":
        open_group(db, site_id=ctx.site_id, category="usage_review",
                   group_key=f"usage_review:{row.machine_id}:{pattern}:{finding['local_date']}",
                   title=f"Needs review: {pattern.replace('_', ' ')} on {row.machine_id}",
                   summary=", ".join(finding.get("possible_explanations", [])) or pattern,
                   priority=3, at=row.observed_at, machine_id=row.machine_id, related_id=root)


def _set_field(fields: dict[str, Any], name: str, value: Any, source: str, entry_id: str) -> None:
    """IncidentFields precedence (§5.3.3): reviewed > reported > inferred > observed."""
    if value is None:
        return
    current = fields.get(name)
    if current is None or SOURCE_RANK[source] >= SOURCE_RANK.get(current.get("source", "observed"), 0):
        fields[name] = {"value": value, "source": source, "entry_id": entry_id}


def _incident(db: Session, device: Device, ctx: MachineContext, row: LedgerEntry) -> None:
    p = row.payload
    body = p.get("replacement") if row.kind == "correction" else p
    incident_id = (body or {}).get("incident_id") or p.get("incident_id")
    if row.kind == "correction" and incident_id is None:
        target = db.get(LedgerEntry, row.supersedes) if row.supersedes else None
        incident_id = target.payload.get("incident_id") if target else None
    if incident_id is None:
        return

    inc = db.get(Incident, incident_id)
    if inc is None:
        inc = Incident(incident_id=incident_id, device_id=device.device_id, machine_id=row.machine_id,
                       operator_id=row.operator_id, shift_id=row.shift_id, site_id=ctx.site_id,
                       occurred_at=row.observed_at, status="awaiting_report", origin="auto", fields={},
                       created_at=utc_now(), updated_at=utc_now())
        db.add(inc)
    fields = dict(inc.fields or {})

    if row.kind == "incident" and row.subtype == "created":
        obs = p["observed"]
        inc.origin = p["origin"]
        inc.occurred_at = parse_ts(p["occurred_at"])
        inc.zone_id = p.get("zone_id")
        inc.snapshot = p["snapshot"]
        trigger_types = [a.get("alert_type", "") for a in (p["snapshot"].get("alerts") or [])]
        default_type = "unsafe_condition" if any(t.startswith("A-BELT") for t in trigger_types) else "near_miss"
        _set_field(fields, "type", default_type, "observed", row.entry_id)
        _set_field(fields, "severity", p["severity_default"], "observed", row.entry_id)
        for name in ("machine_state", "speed_kmh", "belt_fastened", "secure_engaged", "conditions"):
            _set_field(fields, name, obs.get(name), "observed", row.entry_id)
        _set_field(fields, "zone_id", p.get("zone_id"), "observed", row.entry_id)
        _set_field(fields, "occurred_at", p["occurred_at"], "observed", row.entry_id)
        detected = obs.get("detected") or []
        if detected:
            _set_field(fields, "object", detected[0].get("type"), "observed", row.entry_id)
            _set_field(fields, "place", detected[0].get("place"), "observed", row.entry_id)
    elif row.kind == "incident" and row.subtype == "snapshot_completed":
        snap = dict(inc.snapshot or {})
        snap["post_samples"] = p.get("post_samples", [])
        snap["truncated"] = p.get("truncated", False)
        inc.snapshot = snap
        inc.snapshot_complete = True
    elif row.kind == "incident" and row.subtype == "status_changed":
        if inc.status != "reviewed":
            inc.status = p["status"]
    elif (row.kind, row.subtype) == ("report", "incident_report") or (
        row.kind == "correction" and row.subtype == "incident_report" and body
    ):
        for name in ("type", "object", "place", "contact", "severity"):
            _set_field(fields, name, body.get(name), "reported", row.entry_id)
        if inc.status == "awaiting_report":
            inc.status = "reported"
    elif (row.kind, row.subtype) == ("inference", "incident_extraction") and not p.get("no_incident"):
        for name, value in (p.get("fields") or {}).items():
            _set_field(fields, name, value, "inferred", row.entry_id)

    inc.fields = fields
    inc.type = (fields.get("type") or {}).get("value")
    inc.severity = (fields.get("severity") or {}).get("value")
    inc.updated_at = utc_now()
    db.flush()

    # Chain verification (§8.10): any failure or gap marks later incidents of this device chain_ok = false
    if row.chain_seq is not None:
        bad = first_bad_chain_seq(db, device.device_id)
        _apply_chain_result(db, ctx, device, bad)

    # Safety follow-up per incident, and the near-miss zone cluster rule (§8.21)
    open_group(db, site_id=ctx.site_id, category="safety_incident", group_key=f"incident:{incident_id}",
               title=f"Incident: {(inc.type or 'unreported').replace('_', ' ')} on {row.machine_id}",
               summary=f"Incident at {_zone_name(db, inc.zone_id) or 'unknown zone'} — status {inc.status}.",
               priority=1 if inc.type == "contact_person" or inc.severity == "high" else 2,
               at=row.observed_at, machine_id=row.machine_id, zone_id=inc.zone_id, related_id=incident_id)
    if inc.type == "near_miss" and inc.zone_id:
        since = inc.occurred_at - timedelta(days=7)
        count = db.query(Incident).filter(Incident.zone_id == inc.zone_id, Incident.type == "near_miss",
                                          Incident.occurred_at >= since).count()
        if count >= 2:
            open_group(db, site_id=ctx.site_id, category="near_miss_cluster",
                       group_key=f"near_miss_cluster:{inc.zone_id}",
                       title=f"Near-misses clustered at {_zone_name(db, inc.zone_id)}",
                       summary=f"{count} near-misses in this zone within 7 days.", priority=1, at=row.observed_at,
                       zone_id=inc.zone_id, metrics={"count": count})


def _apply_chain_result(db: Session, ctx: MachineContext, device: Device, bad_seq: int | None) -> None:
    incidents = db.query(Incident).filter(Incident.device_id == device.device_id).all()
    for inc in incidents:
        seqs = [r.chain_seq for r in db.query(LedgerEntry).filter(
            LedgerEntry.device_id == device.device_id, LedgerEntry.chain_seq.isnot(None)).all()
            if (r.payload or {}).get("incident_id") == inc.incident_id
            or ((r.payload or {}).get("replacement") or {}).get("incident_id") == inc.incident_id]
        inc.chain_ok = bad_seq is None or all(s < bad_seq for s in seqs)
    if bad_seq is not None:
        open_group(db, site_id=ctx.site_id, category="chain_integrity",
                   group_key=f"chain_integrity:{device.device_id}",
                   title=f"Incident record integrity issue on {device.machine_id}",
                   summary=f"Hash chain fails or has a gap at sequence {bad_seq}.", priority=1,
                   at=utc_now(), machine_id=device.machine_id, related_id=device.device_id)


def _overspeed_zone(db: Session, ctx: MachineContext, row: LedgerEntry) -> None:
    zone_id = row.payload["zone_id"]
    since = row.observed_at - timedelta(days=7)
    rows = db.query(LedgerEntry).filter(LedgerEntry.kind == "alert", LedgerEntry.subtype == "raised",
                                        LedgerEntry.observed_at >= since).all()
    operators = {r.operator_id for r in rows
                 if r.payload.get("alert_type") == "A-SPEED" and r.payload.get("zone_id") == zone_id and r.operator_id}
    if len(operators) >= 3:
        open_group(db, site_id=ctx.site_id, category="overspeed_zone", group_key=f"overspeed_zone:{zone_id}",
                   title=f"Overspeed by several operators at {_zone_name(db, zone_id)}",
                   summary=f"{len(operators)} operators over the limit in 7 days — check limit and signage.",
                   priority=2, at=row.observed_at, zone_id=zone_id, metrics={"operators": len(operators)})


def _report(db: Session, ctx: MachineContext, row: LedgerEntry) -> tuple[str, str | None]:
    p, subtype = row.payload, row.subtype
    if subtype == "alert_feedback":
        open_group(db, site_id=ctx.site_id, category="alert_review",
                   group_key=f"alert_review:{p['alert_type']}:{row.machine_id}:{local_date(ctx, row.observed_at)}",
                   title=f"Alert feedback: {p['alert_type']} marked {p['feedback']}",
                   summary=f"Operator marked alert {p['alert_id']} as {p['feedback']}.", priority=3,
                   at=row.observed_at, machine_id=row.machine_id, related_id=p["alert_id"])
    elif subtype == "help_request":
        db.merge(HelpRequest(request_id=row.entry_id, operator_id=row.operator_id or "", machine_id=row.machine_id,
                             content_id=p["content_id"], question_text=p.get("question_text"), status="open",
                             created_at=row.observed_at))
        open_group(db, site_id=ctx.site_id, category="help_request", group_key=f"help:{row.entry_id}",
                   title=f"Help request on {p['content_id']}",
                   summary=p.get("question_text") or "Operator asked for a trainer after two wrong answers.",
                   priority=3, at=row.observed_at, machine_id=row.machine_id, related_id=row.entry_id)
    elif subtype == "reassignment_request":
        if db.get(TaskAssignment, p["task_id"]) is None:
            raise Rejected("unknown_task")
        db.merge(ReassignmentRequest(request_id=row.entry_id, task_id=p["task_id"], machine_id=row.machine_id,
                                     operator_id=row.operator_id or "", reason_code=p["reason_code"],
                                     status="pending", created_at=row.observed_at))
        risk = (p.get("impact") or {}).get("risk")
        open_group(db, site_id=ctx.site_id, category="assignment_request", group_key=f"reassign:{row.entry_id}",
                   title=f"Reassignment requested for {p['task_id']}",
                   summary=f"Reason: {p['reason_code'].replace('_', ' ')}" + (f"; next task risk: {risk}" if risk else ""),
                   priority=2, at=row.observed_at, machine_id=row.machine_id, related_id=row.entry_id)
    elif subtype == "supervisor_notification":
        impact = p["impact"]
        risk = impact.get("risk", "unavailable")
        risk_text = {"likely_miss": "likely to miss its start window", "at_risk": "at risk of missing its start window",
                     "none": "on time", "unavailable": "impact unavailable"}.get(risk, risk)
        open_group(db, site_id=ctx.site_id, category="supervisor_notification", group_key=f"notify:{row.entry_id}",
                   title=f"{p['task_id']} delayed +{impact.get('current_delta_min', 0)} min — next task {risk_text}",
                   summary=f"Reason: {str(p['reason_code']).replace('_', ' ')}.",
                   priority=2 if risk == "likely_miss" else 3, at=row.observed_at, machine_id=row.machine_id,
                   related_id=row.entry_id, metrics={"impact": impact})
    return "confirmed", None


def _handover_bundle(db: Session, device: Device, ctx: MachineContext, env: OutboxEnvelope) -> tuple[str, str | None]:
    body = env.body
    handover, items = body.handover or {}, body.items or []
    handover_id = handover.get("handover_id")
    if not handover_id:
        raise Rejected("missing_handover")
    if handover.get("machine_id") != device.machine_id:
        raise Rejected("machine_mismatch")
    if db.get(Handover, handover_id) is not None:
        return "duplicate", None
    db.add(Handover(handover_id=handover_id, machine_id=device.machine_id,
                    from_shift_id=handover.get("from_shift_id"), from_operator_id=handover.get("from_operator_id"),
                    device_id=device.device_id, voice_note_upload_id=handover.get("voice_note_upload_id"),
                    wording_method=handover.get("wording_method", "template"),
                    created_at=parse_ts(handover.get("created_at")), data_origin="live"))
    for item in items:
        if "operator_only" in (item.get("audiences") or []):
            raise Rejected("private_not_accepted")
        db.add(HandoverItem(item_id=item["item_id"], handover_id=handover_id, item_type=item["item_type"],
                            text=item["text"], audiences=item["audiences"],
                            source_entry_ids=item.get("source_entry_ids", []), task_id=item.get("task_id"),
                            incident_id=item.get("incident_id"), carried_from_item_id=item.get("carried_from_item_id"),
                            status="open"))
    db.flush()
    record_change(db, "handover.published", "machine", device.machine_id, {"handover": handover, "items": items})
    return "confirmed", None


# ----------------------------------------------------------------------------------------------- helpers


def _zone_name(db: Session, zone_id: str | None) -> str | None:
    if not zone_id:
        return None
    zone = db.get(Zone, zone_id)
    return zone.name if zone else zone_id


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


__all__ = ["project_envelope", "parse_ts", "wire_sha256", "Rejected", "Machine", "Site", "FollowUp"]
