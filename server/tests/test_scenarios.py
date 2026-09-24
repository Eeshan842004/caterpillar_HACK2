"""Near miss → scenario pipeline, server side (§8.23, §6.3 C4; TC-54)."""

import uuid

from shiftmate.models import Incident, Scenario
from shiftmate.services.scenarios import TEMPLATES, scenario_id_for, template_id
from tests.conftest import console_login, entry, make_device_auth_headers, pair, push
from tests.test_projections import _chain, _incident_entries

H = {"X-Requested-With": "shiftmate-console"}


def _near_miss(client, device_id, secret, *, rain=False, place="rear"):
    incident_id = str(uuid.uuid4())
    created, report = _incident_entries(device_id, incident_id)
    created["payload"]["observed"]["conditions"] = {"rain": rain, "dust": False, "darkness": False}
    report["payload"]["place"] = place
    results = push(client, device_id, secret, _chain([created, report]))
    assert {r["status"] for r in results.values()} == {"confirmed"}
    return incident_id


def _pull(client, device_id, secret):
    path = "/api/v1/sync/pull?cursor=0&limit=500"
    return client.get(path, headers=make_device_auth_headers("GET", path, b"", device_id, secret)).json()[
        "changes"
    ]


def test_tc54_review_draft_edit_approve_publishes_to_excavators(client, db):
    device_id, secret = pair(client)
    incident_id = _near_miss(client, device_id, secret, rain=True, place="rear_left")

    # Safety review of a near miss → template draft in en + hi
    console_login(client, "saf.meena", "Meena-Demo-2026")
    res = client.post(
        f"/api/v1/console/incidents/{incident_id}/review",
        json={"field_corrections": {}, "note": None},
        headers=H,
    )
    assert res.status_code == 200, res.text
    scenario_id = res.json()["scenario_id"]
    assert (
        scenario_id == scenario_id_for(incident_id)
        and scenario_id.startswith("nm-")
        and len(scenario_id) == 11
    )
    draft = db.get(Scenario, scenario_id)
    assert (draft.status, draft.draft_method, draft.machine_class) == ("draft", "template", "excavator")
    body = draft.body
    assert set(body["localized"]) == {"en", "hi"}
    assert body["title"] == "Near miss: worker rear left"
    assert (
        "You are digging with the excavator at the trench area. It has started to rain. "
        "A worker walks toward your machine from the rear left." in body["situation"]
    )
    en_choices = [c["text"] for c in body["choices"]]
    assert body["choices"][body["correct_index"]]["text"] == TEMPLATES["T-EX-PERSON"]["en"][0][0]
    assert sorted(en_choices) == sorted(t for t, _ in TEMPLATES["T-EX-PERSON"]["en"])
    hi = body["localized"]["hi"]
    assert hi["correct_index"] == body["correct_index"] and hi["translation_status"] == "draft"
    # Anonymised: no operator, machine, zone name or exact time
    text = str(body)
    for secret_text in ("EX-07", "OP-0007", "Ravi", "Trench Area T1", "T1", incident_id):
        assert secret_text not in text

    # Trainer reads the draft with its anonymised source summary, edits it, approves it
    console_login(client, "trn.arjun", "Arjun-Demo-2026")
    detail = client.get(f"/api/v1/console/scenarios/{scenario_id}").json()
    assert detail["source_summary"] == {
        "type": "near_miss",
        "object": "person",
        "place": "rear_left",
        "time_of_day": detail["source_summary"]["time_of_day"],
        "zone_kind": "trench_area",
        "conditions": ["rain"],
    }
    edited = detail["body"]
    edited["localized"]["en"]["title"] = "Near miss: worker behind the excavator"
    res = client.put(f"/api/v1/console/scenarios/{scenario_id}", json={"body": edited}, headers=H)
    assert res.status_code == 200, res.text
    assert res.json()["body"]["title"] == "Near miss: worker behind the excavator"  # top level mirrors en

    res = client.post(f"/api/v1/console/scenarios/{scenario_id}/approve", headers=H)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "approved" and res.json()["published_change_seq"]
    assert (
        client.put(f"/api/v1/console/scenarios/{scenario_id}", json={"body": edited}, headers=H).status_code
        == 409
    )

    # The change reaches an excavator device on /sync/pull (scope machine_class)
    published = [
        c
        for c in _pull(client, device_id, secret)
        if c["change_type"] == "scenario.published" and c["payload"]["scenario_id"] == scenario_id
    ]
    assert len(published) == 1
    assert (published[0]["scope_type"], published[0]["scope_id"]) == ("machine_class", "excavator")
    assert published[0]["payload"]["title"] == "Near miss: worker behind the excavator"
    assert published[0]["payload"]["source"] == "near_miss"


def test_put_validates_three_choices_and_correct_index(client, db):
    device_id, secret = pair(client)
    incident_id = _near_miss(client, device_id, secret)
    console_login(client, "saf.meena", "Meena-Demo-2026")
    client.post(f"/api/v1/console/incidents/{incident_id}/send-to-trainer", headers=H)
    scenario_id = db.get(Incident, incident_id).scenario_id
    assert scenario_id == scenario_id_for(incident_id)

    console_login(client, "trn.arjun", "Arjun-Demo-2026")
    body = client.get(f"/api/v1/console/scenarios/{scenario_id}").json()["body"]
    two = {
        **body,
        "localized": {**body["localized"], "en": {**body["localized"]["en"], "choices": body["choices"][:2]}},
    }
    assert (
        client.put(f"/api/v1/console/scenarios/{scenario_id}", json={"body": two}, headers=H).status_code
        == 422
    )
    bad = {**body, "localized": {**body["localized"], "en": {**body["localized"]["en"], "correct_index": 3}}}
    assert (
        client.put(f"/api/v1/console/scenarios/{scenario_id}", json={"body": bad}, headers=H).status_code
        == 422
    )
    moved = {**body, "content_id": "nm-00000000"}
    assert (
        client.put(f"/api/v1/console/scenarios/{scenario_id}", json={"body": moved}, headers=H).status_code
        == 422
    )


def test_roles_redraft_reject_and_llm_unavailable(client, db):
    device_id, secret = pair(client)
    incident_id = _near_miss(client, device_id, secret)
    console_login(client, "saf.meena", "Meena-Demo-2026")
    client.post(f"/api/v1/console/incidents/{incident_id}/review", json={"field_corrections": {}}, headers=H)
    scenario_id = scenario_id_for(incident_id)
    assert client.get(f"/api/v1/console/scenarios/{scenario_id}").status_code == 200  # safety reads
    assert client.post(f"/api/v1/console/scenarios/{scenario_id}/approve", headers=H).status_code == 403

    console_login(client, "mec.dinesh", "Dinesh-Demo-2026")
    assert client.get("/api/v1/console/scenarios").status_code == 403

    console_login(client, "trn.arjun", "Arjun-Demo-2026")
    res = client.post(f"/api/v1/console/scenarios/{scenario_id}/redraft", json={"method": "llm"}, headers=H)
    assert res.status_code == 409 and "AI unavailable" in res.json()["error"]["message"]
    res = client.post(
        f"/api/v1/console/scenarios/{scenario_id}/reject", json={"reason": "duplicate"}, headers=H
    )
    assert res.json()["status"] == "rejected"
    assert client.post(f"/api/v1/console/scenarios/{scenario_id}/approve", headers=H).status_code == 409
    res = client.post(
        f"/api/v1/console/scenarios/{scenario_id}/redraft", json={"method": "template"}, headers=H
    )
    assert (
        res.status_code == 200 and res.json()["status"] == "draft" and res.json()["rejected_reason"] is None
    )
    listed = client.get("/api/v1/console/scenarios", params={"status": "draft"}).json()["items"]
    assert scenario_id in [s["scenario_id"] for s in listed]


def test_template_selection():
    assert template_id("excavator", "person") == "T-EX-PERSON"
    assert template_id("excavator", "heavy_vehicle") == "T-EX-VEHICLE"
    assert template_id("haul_truck", "person") == "T-HT-PERSON"
    assert template_id("haul_truck", "light_vehicle") == "T-HT-LV"
    assert template_id("haul_truck", "heavy_vehicle") == "T-GENERIC"
    assert template_id("wheel_loader", "person") == "T-GENERIC"
    for lang in ("en", "hi"):
        for choices in TEMPLATES.values():
            assert len(choices[lang]) == 3
            assert all(len(t) <= 90 and len(e) <= 200 for t, e in choices[lang])


def test_non_near_miss_review_creates_no_draft(client, db):
    device_id, secret = pair(client)
    incident_id = str(uuid.uuid4())
    created, _ = _incident_entries(device_id, incident_id)
    report = entry(
        device_id,
        "EX-07",
        "report",
        "incident_report",
        "reported",
        {
            "incident_id": incident_id,
            "type": "machine_fault",
            "object": "unknown",
            "place": "unknown",
            "contact": "no",
            "severity": "low",
            "via": "button",
        },
        audience="safety",
    )
    push(client, device_id, secret, _chain([created, report]))
    console_login(client, "saf.meena", "Meena-Demo-2026")
    res = client.post(
        f"/api/v1/console/incidents/{incident_id}/review", json={"field_corrections": {}}, headers=H
    )
    assert res.status_code == 200 and res.json()["scenario_id"] is None
    assert db.get(Scenario, scenario_id_for(incident_id)) is None
