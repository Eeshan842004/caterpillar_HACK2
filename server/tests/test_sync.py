"""Sync push/pull (TC-45, TC-46, TC-51) and the push-handling bugs from the audit."""

import json
import uuid

from tests.conftest import entry, make_device_auth_headers, now_iso, pair, push


def test_push_rules_and_idempotency(client):
    device_id, secret = pair(client)
    idle = entry(
        device_id,
        "EX-07",
        "report",
        "idle_reason",
        "reported",
        {
            "idle_event_id": str(uuid.uuid4()),
            "reason_code": "waiting_truck",
            "free_text": None,
            "via": "button",
        },
    )
    start = entry(
        device_id,
        "EX-07",
        "task_event",
        "start",
        "reported",
        {"task_id": "T-20260923-EX07-1", "assignment_revision": 1},
    )
    private = entry(
        device_id,
        "EX-07",
        "learning_event",
        "completed",
        "reported",
        {"content_id": "ex-l-belt-lockout"},
        audience="operator_only",
    )
    other_machine = entry(
        device_id,
        "HT-03",
        "task_event",
        "start",
        "reported",
        {"task_id": "T-20260923-HT03-1", "assignment_revision": 1},
    )
    bad_payload = entry(
        device_id,
        "EX-07",
        "report",
        "idle_reason",
        "reported",
        {"idle_event_id": "x", "reason_code": "coffee"},
    )
    no_rule = entry(
        device_id,
        "EX-07",
        "alert",
        "raised",
        "observed",
        {"alert_id": "a1", "alert_type": "A-BELT-OPER", "level": "WARNING", "group_key": "belt"},
    )
    bad_time = entry(
        device_id, "EX-07", "shift_event", "end", "reported", {"handover_id": None}, at="yesterday"
    )
    server_only = entry(
        device_id, "EX-07", "incident", "reviewed", "reviewed", {"incident_id": "i1"}, audience="safety"
    )

    results = push(
        client,
        device_id,
        secret,
        [idle, start, private, other_machine, bad_payload, no_rule, bad_time, server_only],
    )
    assert results[idle["entry_id"]]["status"] == "confirmed"
    assert results[start["entry_id"]]["status"] == "confirmed"
    assert results[private["entry_id"]]["reason"] == "private_not_accepted"
    assert results[other_machine["entry_id"]]["reason"] == "machine_mismatch"
    assert results[bad_payload["entry_id"]]["reason"].startswith("validation_error")
    assert results[no_rule["entry_id"]]["reason"] == "missing_rule_version"
    assert results[bad_time["entry_id"]]["reason"] == "invalid_timestamp"  # never silently replaced by "now"
    assert results[server_only["entry_id"]]["reason"] == "server_only_subtype"

    # Same batch again → duplicate (not a second row); same id with a different payload → rejected (TC-45)
    again = push(client, device_id, secret, [idle, start])
    assert {r["status"] for r in again.values()} == {"duplicate"}
    changed = dict(idle, payload={**idle["payload"], "reason_code": "access_blocked"})
    assert (
        push(client, device_id, secret, [changed])[idle["entry_id"]]["reason"] == "id_reuse_different_payload"
    )


def test_one_bad_entry_does_not_fail_the_batch(client):
    device_id, secret = pair(client)
    good = entry(device_id, "EX-07", "shift_event", "end", "reported", {"handover_id": None})
    unknown_task = entry(
        device_id,
        "EX-07",
        "report",
        "reassignment_request",
        "reported",
        {"task_id": "T-NOPE", "reason_code": "machine_fault"},
    )
    results = push(client, device_id, secret, [unknown_task, good])
    assert results[unknown_task["entry_id"]]["status"] == "rejected"
    assert results[good["entry_id"]]["status"] == "confirmed"


def test_pull_uses_machine_class_from_profile(client, db):
    """Audit bug 1: 'haul_truck_90t'.split('_')[0] == 'haul', so trucks never got machine_class changes."""
    from shiftmate.services.changes import record_change

    record_change(db, "scenario.published", "machine_class", "haul_truck", {"scenario_id": "nm-test"})
    db.commit()
    device_id, secret = pair(client, "300003", "HT-03")
    path = "/api/v1/sync/pull?cursor=0&limit=500"
    res = client.get(path, headers=make_device_auth_headers("GET", path, b"", device_id, secret))
    assert res.status_code == 200
    assert any(c["payload"].get("scenario_id") == "nm-test" for c in res.json()["changes"])


def test_bootstrap_includes_handover_and_site_local_starts(client):
    device_id, secret = pair(client)
    path = "/api/v1/devices/bootstrap"
    data = client.get(path, headers=make_device_auth_headers("GET", path, b"", device_id, secret)).json()
    items = [i for h in data["handovers"] for i in h["items"]]
    assert {i["item_type"] for i in items} >= {"blocked_task", "defect"}
    task2 = next(t for t in data["assignments"] if t["task_id"].endswith("EX07-2"))
    # 14:10 site-local (+05:30) is 08:40 UTC
    assert task2["planned_start_at"].endswith("T08:40:00.000Z")
    assert all(m["machine_class"] in ("excavator", "wheel_loader", "haul_truck") for m in data["machines"])


def test_handover_bundle_is_stored(client):
    device_id, secret = pair(client)
    handover_id = str(uuid.uuid4())
    batch = {
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
                        "from_shift_id": None,
                        "from_operator_id": "OP-0007",
                        "created_at": now_iso(),
                        "voice_note_upload_id": None,
                        "wording_method": "template",
                    },
                    "items": [
                        {
                            "item_id": str(uuid.uuid4()),
                            "item_type": "note",
                            "text": "Soft ground east edge",
                            "audiences": ["next_operator"],
                            "source_entry_ids": [],
                        }
                    ],
                },
            }
        ]
    }
    body = json.dumps(batch).encode()
    headers = make_device_auth_headers("POST", "/api/v1/sync/push", body, device_id, secret)
    headers["Content-Type"] = "application/json"
    first = client.post("/api/v1/sync/push", content=body, headers=headers).json()["results"][0]
    assert first["status"] == "confirmed"
    second = client.post(
        "/api/v1/sync/push",
        content=body,
        headers={
            **make_device_auth_headers("POST", "/api/v1/sync/push", body, device_id, secret),
            "Content-Type": "application/json",
        },
    ).json()["results"][0]
    assert second["status"] == "duplicate"
