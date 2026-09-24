"""Server projections (§8.21): explain-once follow-up aggregation, corrections, conflicts, incident chain."""

import hashlib
import json
import uuid
from datetime import UTC, datetime

from tests.conftest import console_login, entry, pair, push


def _finding(machine_id, zone_id, reason, minutes, local_date="2026-09-23"):
    return {
        "finding_id": str(uuid.uuid4()),
        "subject_id": str(uuid.uuid4()),
        "pattern_code": "idle_reported_wait",
        "owner": "site",
        "evidence_status": "reported",
        "reason_key": "finding.idle_reported_wait",
        "observed": {"text_key": "finding.observed.idle_wait", "params": {}},
        "possible_explanations": [reason],
        "related_entry_ids": [],
        "machine_id": machine_id,
        "site_id": "SITE-CHN-01",
        "zone_id": zone_id,
        "reason_code": reason,
        "minutes": minutes,
        "local_date": local_date,
        "rule_version": "findings@1",
    }


def test_site_delay_follow_up_groups_and_moves_on_correction(client, db):
    """TC-48 / J5: 3 truck waits (15, 20, 20) → one follow-up 3 / 55 min; correcting one → 2 / 35 + new group."""
    from shiftmate.models import FollowUp

    device_id, secret = pair(client)
    findings = [
        entry(
            device_id,
            "EX-07",
            "inference",
            "finding",
            "inferred",
            _finding("EX-07", "Z-CHN-LB2", "waiting_truck", m),
            rule_or_model_version="findings@1",
        )
        for m in (15, 20, 20)
    ]
    push(client, device_id, secret, findings)
    fu = (
        db.query(FollowUp)
        .filter(FollowUp.group_key == "site_delay:SITE-CHN-01:Z-CHN-LB2:waiting_truck:2026-09-23")
        .one()
    )
    assert fu.metrics == {"count": 3, "total_minutes": 55.0}
    assert fu.title == "Truck wait at Loading Bay 2 — 3 reports, 55 min total today"

    replacement = dict(
        findings[0]["payload"], reason_code="access_blocked", possible_explanations=["access_blocked"]
    )
    correction = entry(
        device_id,
        "EX-07",
        "correction",
        "finding",
        "inferred",
        {"target_kind": "inference", "target_subtype": "finding", "replacement": replacement},
        supersedes=findings[0]["entry_id"],
        rule_or_model_version="findings@1",
    )
    push(client, device_id, secret, [correction])
    db.expire_all()
    assert db.get(FollowUp, fu.follow_up_id).metrics == {"count": 2, "total_minutes": 40.0}
    moved = (
        db.query(FollowUp)
        .filter(FollowUp.group_key == "site_delay:SITE-CHN-01:Z-CHN-LB2:access_blocked:2026-09-23")
        .one()
    )
    assert moved.metrics == {"count": 1, "total_minutes": 15.0}


def test_offline_completion_of_reassigned_task_is_a_conflict(client, db):
    """TC-47: a task_event with an old revision after reassignment → needs_review + sync_conflict follow-up."""
    from shiftmate.models import FollowUp, TaskAssignment

    task = (
        db.get(TaskAssignment, "T-20260923-EX07-2")
        or db.query(TaskAssignment)
        .filter(TaskAssignment.machine_id == "EX-07", TaskAssignment.sequence == 2)
        .one()
    )
    task.machine_id, task.revision = "EX-01", 2
    db.commit()
    device_id, secret = pair(client)
    done = entry(
        device_id,
        "EX-07",
        "task_event",
        "complete",
        "reported",
        {"task_id": task.task_id, "assignment_revision": 1, "output_qty": 60.0},
    )
    result = push(client, device_id, secret, [done])[done["entry_id"]]
    assert result == {"entry_id": done["entry_id"], "status": "needs_review", "reason": "assignment_changed"}
    assert db.query(FollowUp).filter(FollowUp.group_key == f"sync_conflict:{done['entry_id']}").count() == 1
    task.machine_id, task.revision = "EX-07", 1
    db.commit()


def _chain(entries):
    prev = "0" * 64
    for i, e in enumerate(entries, start=1):
        ms = lambda s: int(datetime.fromisoformat(s).timestamp() * 1000)
        body = {
            k: e[k]
            for k in (
                "entry_id",
                "device_id",
                "shift_id",
                "machine_id",
                "operator_id",
                "kind",
                "subtype",
                "source",
                "payload",
            )
        }
        body.update(
            observed_at=ms(e["observed_at"]),
            recorded_at=ms(e["recorded_at"]),
            supersedes=None,
            original_text=None,
        )
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        e.update(
            chain_seq=i,
            prev_hash=prev,
            canonical_payload=canonical,
            content_hash=hashlib.sha256((prev + "\n" + canonical).encode()).hexdigest(),
        )
        prev = e["content_hash"]
    return entries


def _incident_entries(device_id, incident_id):
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    created = entry(
        device_id,
        "EX-07",
        "incident",
        "created",
        "observed",
        {
            "incident_id": incident_id,
            "origin": "auto",
            "trigger_alert_id": "a1",
            "occurred_at": now,
            "zone_id": "Z-CHN-TR1",
            "observed": {
                "machine_state": "WORKING",
                "speed_kmh": 1.0,
                "detected": [{"object_id": "P1", "type": "person", "place": "rear", "min_distance_m": 3.1}],
            },
            "snapshot": {
                "pre_s": 60,
                "post_s": 30,
                "samples": [],
                "proximity": [],
                "alerts": [{"ts": 0, "alert_type": "A-PROX-WARN", "level": "WARNING"}],
            },
            "snapshot_complete": False,
            "severity_default": "high",
        },
        audience="safety",
    )
    report = entry(
        device_id,
        "EX-07",
        "report",
        "incident_report",
        "reported",
        {
            "incident_id": incident_id,
            "type": "near_miss",
            "object": "person",
            "place": "rear",
            "contact": "no",
            "severity": "high",
            "via": "voice",
        },
        audience="safety",
    )
    return created, report


def test_incident_chain_verifies_and_tampering_is_detected(client, db):
    """TC-49: §8.10 chain; a tampered payload on the next device flips chain_ok and opens chain_integrity."""
    from shiftmate.models import FollowUp, Incident

    device_id, secret = pair(client, "100007", "EX-07")
    incident_id = str(uuid.uuid4())
    created, report = _chain(list(_incident_entries(device_id, incident_id)))
    results = push(client, device_id, secret, [created, report])
    assert {r["status"] for r in results.values()} == {"confirmed"}
    inc = db.get(Incident, incident_id)
    assert inc.chain_ok and inc.status == "reported" and inc.type == "near_miss"
    assert inc.fields["object"] == {"value": "person", "source": "reported", "entry_id": report["entry_id"]}

    # A second (fresh) device whose stored canonical payload no longer matches the entry
    other_id = str(uuid.uuid4())
    res = client.post(
        "/api/v1/devices/pair",
        json={
            "pairing_code": "100007",
            "machine_id": "EX-07",
            "device_label": "t2",
            "client_device_id": other_id,
        },
    )
    other_secret = res.json()["device_secret"]
    bad_incident = str(uuid.uuid4())
    c2, r2 = _chain(list(_incident_entries(other_id, bad_incident)))
    r2["payload"] = dict(r2["payload"], contact="yes")  # tampered after hashing
    push(client, other_id, other_secret, [c2, r2])
    db.expire_all()
    assert db.get(Incident, bad_incident).chain_ok is False
    assert db.query(FollowUp).filter(FollowUp.group_key == f"chain_integrity:{other_id}").count() == 1


def test_incident_review_is_site_scoped_and_writes_ledger(client, db):
    from shiftmate.models import ConsoleUser, Incident, LedgerEntry

    device_id, secret = pair(client)
    incident_id = str(uuid.uuid4())
    push(client, device_id, secret, list(_chain(list(_incident_entries(device_id, incident_id)))))
    console_login(client, "saf.meena", "Meena-Demo-2026")
    res = client.post(
        f"/api/v1/console/incidents/{incident_id}/review",
        json={"field_corrections": {"severity": "medium"}, "note": "checked CCTV"},
        headers={"X-Requested-With": "shiftmate-console"},
    )
    assert res.status_code == 200, res.text
    assert res.json()["incident"]["status"] == "reviewed"
    assert res.json()["incident"]["fields"]["severity"]["source"] == "reviewed"
    reviewed = (
        db.query(LedgerEntry).filter(LedgerEntry.kind == "incident", LedgerEntry.subtype == "reviewed").all()
    )
    assert any(e.payload["incident_id"] == incident_id for e in reviewed)

    # A safety user without SITE-CHN-01 cannot see it (audit: incidents had no site_id)
    user = db.query(ConsoleUser).filter(ConsoleUser.username == "saf.meena").one()
    user.site_ids = ["SITE-MIN-03"]
    db.commit()
    assert client.get(f"/api/v1/console/incidents/{incident_id}").status_code == 404
    user.site_ids = ["SITE-CHN-01", "SITE-BLR-02", "SITE-MIN-03", "SITE-MIN-04"]
    db.commit()
    assert db.get(Incident, incident_id).site_id == "SITE-CHN-01"
