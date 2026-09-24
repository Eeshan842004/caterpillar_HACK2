"""Uploads (TC-59, §5.5), body-size limits (§6.1) and console tasks/machines (T32, §6.3)."""

import base64
import json
import uuid

from shiftmate.models import ChangeLog, TaskAssignment
from tests.conftest import console_login, make_device_auth_headers, pair

H = {"X-Requested-With": "shiftmate-console"}


def _upload(client, device_id, secret, entry_id, size, content_type="audio/mp4"):
    body = json.dumps(
        {
            "entry_id": entry_id,
            "kind": "voice_note",
            "content_type": content_type,
            "data_b64": base64.b64encode(b"\x01" * size).decode(),
        }
    ).encode()
    headers = make_device_auth_headers("POST", "/api/v1/uploads", body, device_id, secret)
    headers["Content-Type"] = "application/json"
    return client.post("/api/v1/uploads", content=body, headers=headers)


def test_tc59_upload_sizes_and_idempotency(client):
    device_id, secret = pair(client)
    entry_id = str(uuid.uuid4())
    ok = _upload(client, device_id, secret, entry_id, 900 * 1024)
    assert ok.status_code == 200, ok.text
    assert ok.json()["size_bytes"] == 900 * 1024
    assert ok.json()["storage_key"].startswith("voice_notes/") and ok.json()["storage_key"].endswith(".m4a")
    again = _upload(client, device_id, secret, entry_id, 900 * 1024)
    assert again.json()["upload_id"] == ok.json()["upload_id"]

    too_big = _upload(client, device_id, secret, str(uuid.uuid4()), int(1.2 * 1024 * 1024))
    assert too_big.status_code == 413 and too_big.json()["error"]["code"] == "payload_too_large"

    # Console playback: stored bytes, stored content type, nosniff
    console_login(client, "sup.priya", "Priya-Demo-2026")
    played = client.get(f"/api/v1/console/uploads/{ok.json()['upload_id']}")
    assert played.status_code == 200 and len(played.content) == 900 * 1024
    assert (
        played.headers["content-type"] == "audio/mp4"
        and played.headers["x-content-type-options"] == "nosniff"
    )


def test_body_limit_for_other_endpoints(client):
    res = client.post(
        "/api/v1/devices/pair", content=b"x" * (1_048_576 + 1), headers={"Content-Type": "application/json"}
    )
    assert res.status_code == 413 and res.json()["error"]["code"] == "payload_too_large"


def test_console_tasks_list_reassign_and_machines(client, db):
    console_login(client, "sup.priya", "Priya-Demo-2026")
    items = client.get("/api/v1/console/tasks", params={"machine_id": "EX-07"}).json()["items"]
    assert items and all(t["machine_id"] == "EX-07" for t in items)
    assert {"exec_state", "actual_start", "active_min", "revision"} <= items[0].keys()
    machines = client.get("/api/v1/console/machines", params={"site_id": "SITE-CHN-01"}).json()["items"]
    target = next(
        m["machine_id"] for m in machines if m["machine_id"] != "EX-07" and m["detail_level"] == "detailed"
    )

    task_id, revision = items[-1]["task_id"], items[-1]["revision"]
    before = db.query(ChangeLog).count()
    res = client.post(
        f"/api/v1/console/tasks/{task_id}/reassign",
        json={"new_machine_id": target, "note": "swap"},
        headers=H,
    )
    assert res.status_code == 200, res.text
    assert (res.json()["machine_id"], res.json()["revision"], res.json()["source"]) == (
        target,
        revision + 1,
        "reassignment",
    )
    new = db.query(ChangeLog).filter(ChangeLog.seq > 0).order_by(ChangeLog.seq.desc()).limit(2).all()
    assert db.query(ChangeLog).count() == before + 2
    assert {(c.change_type, c.scope_id) for c in new} == {
        ("task_assignment.removed", "EX-07"),
        ("task_assignment.upsert", target),
    }

    # Cancel it, then a second change is refused
    res = client.post(f"/api/v1/console/tasks/{task_id}/reassign", json={"new_machine_id": None}, headers=H)
    assert res.json()["status"] == "cancelled"
    assert (
        client.post(
            f"/api/v1/console/tasks/{task_id}/reassign", json={"new_machine_id": None}, headers=H
        ).status_code
        == 409
    )
    db.expire_all()
    assert db.get(TaskAssignment, task_id).status == "cancelled"

    console_login(client, "trn.arjun", "Arjun-Demo-2026")
    assert (
        client.post(
            f"/api/v1/console/tasks/{task_id}/reassign", json={"new_machine_id": None}, headers=H
        ).status_code
        == 403
    )
