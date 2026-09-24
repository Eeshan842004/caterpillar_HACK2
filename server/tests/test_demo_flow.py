"""Demo rehearsal (technical spec §13.2, journeys J1 + J2): the server side of the 5-minute script, end to end, as the
tablet and the console would drive it. If this passes, every server step of the demo has been exercised.

Run on its own before a demo: `uv run pytest tests/test_demo_flow.py -v`.
"""

import base64
import json
import uuid
from datetime import UTC, datetime

from shiftmate.models import FollowUp, Incident
from shiftmate.services.scenarios import scenario_id_for
from tests.conftest import console_login, entry, make_device_auth_headers, now_iso, pair, push
from tests.test_projections import _chain, _incident_entries

H = {"X-Requested-With": "shiftmate-console"}


def _signed_get(client, path, device_id, secret):
    res = client.get(path, headers=make_device_auth_headers("GET", path, b"", device_id, secret))
    assert res.status_code == 200, res.text
    return res.json()


def _signed_post(client, path, body, device_id, secret):
    raw = json.dumps(body).encode()
    headers = make_device_auth_headers("POST", path, raw, device_id, secret)
    headers["Content-Type"] = "application/json"
    res = client.post(path, content=raw, headers=headers)
    assert res.status_code == 200, res.text
    return res.json()


def _pull(client, device_id, secret, cursor=0):
    path = f"/api/v1/sync/pull?cursor={cursor}&limit=500"
    return _signed_get(client, path, device_id, secret)["changes"]


def _finding(site_id, machine_id, zone_id, reason, minutes):
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
        "site_id": site_id,
        "zone_id": zone_id,
        "reason_code": reason,
        "minutes": minutes,
        "local_date": datetime.now(UTC).strftime("%Y-%m-%d"),
        "rule_version": "findings@1",
    }


def test_j1_excavator_day(client, db):
    # 0:00 — pair EX-07 (A0) and bootstrap: previous-shift handover, today's tasks, trained estimator
    device_id, secret = pair(client, "100007", "EX-07")
    boot = _signed_get(client, "/api/v1/devices/bootstrap", device_id, secret)
    handover_items = boot["handovers"][0]["items"]
    assert [i["status"] for i in handover_items] == ["open", "open"]
    assert "Trench T2 blocked" in handover_items[0]["text"]
    tasks = sorted(boot["assignments"], key=lambda t: t["sequence"])
    assert len(tasks) == 3 and tasks[0]["task_type"] == "trenching"
    assert [a["artifact_id"] for a in boot["model_artifacts"]] == ["estimator.excavator@1"]
    cursor = boot["cursor"]

    # Ravi signs in and acknowledges both handover items (acknowledged ≠ resolved)
    shift_id = str(uuid.uuid4())
    start = entry(
        device_id,
        "EX-07",
        "shift_event",
        "start",
        "reported",
        {
            "auth_method": "pin",
            "language": "en",
            "guidance": "guided",
            "profile_id": "excavator_20t",
            "profile_version": 1,
        },
        shift_id=shift_id,
    )
    acks = [
        entry(
            device_id,
            "EX-07",
            "handover_item",
            "acknowledged",
            "reported",
            {"item_id": i["item_id"]},
            audience="next_operator",
            shift_id=shift_id,
        )
        for i in handover_items
    ]
    # 0:30 — original estimate (with task_type) and task start
    t1 = tasks[0]
    estimate = entry(
        device_id,
        "EX-07",
        "inference",
        "estimate",
        "inferred",
        {
            "task_id": t1["task_id"],
            "task_type": "trenching",
            "basis": "comparable_history",
            "baseline_min": 49.7,
            "p10_min": 44.0,
            "p50_min": 52.0,
            "p90_min": 58.0,
            "expected_wait_min": 10,
            "factors": [{"factor": "skill", "pct": 21}],
            "artifact_id": "estimator.excavator@1",
            "personal_offset": None,
            "context": {
                "weather": "clear",
                "visibility": "good",
                "temperature_band": "mild",
                "time_of_day": "afternoon",
                "site_congestion": "medium",
                "darkness": False,
            },
        },
        rule_or_model_version="estimator.excavator@1",
        shift_id=shift_id,
    )
    task_start = entry(
        device_id,
        "EX-07",
        "task_event",
        "start",
        "reported",
        {"task_id": t1["task_id"], "assignment_revision": t1["revision"]},
        shift_id=shift_id,
    )
    batch = [start, *acks, estimate, task_start]
    assert {r["status"] for r in push(client, device_id, secret, batch).values()} == {"confirmed"}
    acked = [
        c
        for c in _pull(client, device_id, secret, cursor)
        if c["change_type"] == "handover_item.acknowledged"
    ]
    assert len(acked) == 2

    # 1:50 — truck wait → site delay + "Notify supervisor" (a request only; assignment unchanged)
    wait = entry(
        device_id,
        "EX-07",
        "inference",
        "finding",
        "inferred",
        _finding("SITE-CHN-01", "EX-07", "Z-CHN-LB2", "waiting_truck", 18),
        rule_or_model_version="f@1",
    )
    notify = entry(
        device_id,
        "EX-07",
        "report",
        "supervisor_notification",
        "reported",
        {
            "task_id": t1["task_id"],
            "reason_code": "waiting_truck",
            "source_entry_id": wait["entry_id"],
            "impact": {"current_task_id": t1["task_id"], "current_delta_min": 18, "risk": "likely_miss"},
        },
    )
    push(client, device_id, secret, [wait, notify])
    # 2:20 — "actually, access blocked": the correction moves the delay; history kept
    replacement = dict(
        wait["payload"], reason_code="access_blocked", possible_explanations=["access_blocked"]
    )
    correction = entry(
        device_id,
        "EX-07",
        "correction",
        "finding",
        "inferred",
        {"target_kind": "inference", "target_subtype": "finding", "replacement": replacement},
        supersedes=wait["entry_id"],
        rule_or_model_version="f@1",
    )
    push(client, device_id, secret, [correction])

    console_login(client, "sup.priya", "Priya-Demo-2026")
    items = client.get("/api/v1/console/follow-ups").json()["items"]
    categories = {(i["category"], i["reason_code"]) for i in items if i["machine_id"] == "EX-07"}
    assert ("site_delay", "access_blocked") in categories
    assert any(i["category"] == "supervisor_notification" for i in items)
    tasks_now = client.get("/api/v1/console/tasks", params={"machine_id": "EX-07"}).json()["items"]
    assert next(t for t in tasks_now if t["task_id"] == t1["task_id"])["revision"] == t1["revision"]

    # 2:40–3:00 — worker from the rear → incident; "log near miss…" → reported
    incident_id = str(uuid.uuid4())
    push(client, device_id, secret, _chain(list(_incident_entries(device_id, incident_id))))
    assert db.get(Incident, incident_id).status == "reported"

    # 3:20 — safety reviews (→ template draft), trainer approves, tablet pulls the published scenario
    console_login(client, "saf.meena", "Meena-Demo-2026")
    review = client.post(
        f"/api/v1/console/incidents/{incident_id}/review", json={"field_corrections": {}}, headers=H
    ).json()
    assert review["scenario_id"] == scenario_id_for(incident_id)
    console_login(client, "trn.arjun", "Arjun-Demo-2026")
    approved = client.post(f"/api/v1/console/scenarios/{review['scenario_id']}/approve", headers=H).json()
    assert approved["status"] == "approved"
    published = [
        c for c in _pull(client, device_id, secret, cursor) if c["change_type"] == "scenario.published"
    ]
    assert published[-1]["payload"]["scenario_id"] == review["scenario_id"]

    # 3:50 — offline: the tablet re-sends its queue after reconnecting → every record lands exactly once
    again = push(client, device_id, secret, [*batch, wait, notify, correction])
    assert {r["status"] for r in again.values()} == {"duplicate"}

    # 4:10 — handover with a voice note; Kumar signs in and acknowledges (items stay open)
    note = _signed_post(
        client,
        "/api/v1/uploads",
        {
            "entry_id": str(uuid.uuid4()),
            "kind": "voice_note",
            "content_type": "audio/webm",
            "data_b64": base64.b64encode(b"\x1a" * 4000).decode(),
        },
        device_id,
        secret,
    )
    handover_id, item_id = str(uuid.uuid4()), str(uuid.uuid4())
    bundle = {
        "batch": [
            {
                "entry_id": handover_id,
                "type": "handover",
                "created_at": now_iso(),
                "body": {
                    "kind": "handover_bundle",
                    "handover": {
                        "handover_id": handover_id,
                        "machine_id": "EX-07",
                        "from_shift_id": shift_id,
                        "from_operator_id": "OP-0007",
                        "created_at": now_iso(),
                        "voice_note_upload_id": note["upload_id"],
                        "wording_method": "template",
                    },
                    "items": [
                        {
                            "item_id": item_id,
                            "item_type": "incident",
                            "text": "Near miss at the trench: worker behind",
                            "audiences": ["next_operator", "safety"],
                            "incident_id": incident_id,
                        }
                    ],
                },
            }
        ]
    }
    assert (
        _signed_post(client, "/api/v1/sync/push", bundle, device_id, secret)["results"][0]["status"]
        == "confirmed"
    )
    kumar_ack = entry(
        device_id,
        "EX-07",
        "handover_item",
        "acknowledged",
        "reported",
        {"item_id": item_id},
        audience="next_operator",
        operator_id="OP-0011",
    )
    push(client, device_id, secret, [kumar_ack])
    console_login(client, "sup.priya", "Priya-Demo-2026")
    handovers = client.get("/api/v1/console/handovers").json()["items"]
    ours = next(h for h in handovers if h["handover"]["handover_id"] == handover_id)
    assert ours["handover"]["voice_note_upload_id"] == note["upload_id"]
    assert ours["items"][0]["acknowledged_by"] == "OP-0011" and ours["items"][0]["status"] == "open"
    assert client.get(f"/api/v1/console/uploads/{note['upload_id']}").status_code == 200


def test_j2_haul_truck_switch(client, db):
    # 4:30 — Switch machine → HT-03 (code 300003): Senthil, haul truck estimator, mining site
    device_id, secret = pair(client, "300003", "HT-03")
    boot = _signed_get(client, "/api/v1/devices/bootstrap", device_id, secret)
    assert boot["site"]["site_id"] == "SITE-MIN-03"
    assert [a["artifact_id"] for a in boot["model_artifacts"]] == ["estimator.haul_truck@1"]

    overspeed = entry(
        device_id,
        "HT-03",
        "alert",
        "raised",
        "observed",
        {
            "alert_id": str(uuid.uuid4()),
            "alert_type": "A-SPEED",
            "level": "WARNING",
            "group_key": "speed:Z-MIN-R3",
            "zone_id": "Z-MIN-R3",
        },
        rule_or_model_version="speed@1",
        operator_id="OP-0021",
    )
    queue = entry(
        device_id,
        "HT-03",
        "inference",
        "finding",
        "inferred",
        _finding("SITE-MIN-03", "HT-03", "Z-MIN-SH1", "shovel_queue", 12),
        rule_or_model_version="f@1",
        operator_id="OP-0021",
    )
    assert {r["status"] for r in push(client, device_id, secret, [overspeed, queue]).values()} == {
        "confirmed"
    }
    fu = (
        db.query(FollowUp)
        .filter(
            FollowUp.category == "site_delay",
            FollowUp.machine_id == "HT-03",
            FollowUp.reason_code == "shovel_queue",
        )
        .one()
    )
    assert fu.site_id == "SITE-MIN-03" and fu.metrics["count"] >= 1
    changes = _pull(client, device_id, secret)
    assert not any(c["change_type"] == "scenario.published" and c["scope_id"] == "excavator" for c in changes)
