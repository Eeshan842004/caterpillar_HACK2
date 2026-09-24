"""`publish-models` (T36/T20): bundled artifacts land in `model_artifacts`, publish a `model.published` change
once, and reach a paired device through bootstrap and pull."""

import json

from shiftmate.models import ChangeLog, ModelArtifact
from shiftmate.seed import publish_models
from tests.conftest import make_device_auth_headers, pair


def test_seed_publishes_estimators(db):
    rows = {a.artifact_id: a for a in db.query(ModelArtifact).all()}
    assert {"estimator.excavator@1", "estimator.haul_truck@1"} <= rows.keys()
    assert rows["estimator.excavator@1"].machine_class == "excavator"
    changes = db.query(ChangeLog).filter(ChangeLog.change_type == "model.published").all()
    assert {(c.scope_type, c.scope_id) for c in changes} >= {
        ("machine_class", "excavator"),
        ("machine_class", "haul_truck"),
    }


def test_publish_models_is_idempotent(db):
    before = db.query(ChangeLog).count()
    assert publish_models(db) == []
    db.commit()
    assert db.query(ChangeLog).count() == before


def test_excavator_device_receives_estimator(client):
    device_id, secret = pair(client)
    headers = make_device_auth_headers("GET", "/api/v1/devices/bootstrap", b"", device_id, secret)
    boot = client.get("/api/v1/devices/bootstrap", headers=headers)
    assert boot.status_code == 200, boot.text
    ids = [a["artifact_id"] for a in boot.json()["model_artifacts"]]
    assert "estimator.excavator@1" in ids and "estimator.haul_truck@1" not in ids

    path = "/api/v1/sync/pull?cursor=0&limit=500"
    pulled = client.get(path, headers=make_device_auth_headers("GET", path, b"", device_id, secret)).json()
    published = [c for c in pulled["changes"] if c["change_type"] == "model.published"]
    assert [c["payload"]["artifact_id"] for c in published] == ["estimator.excavator@1"]
    assert json.dumps(published[0]["payload"]["coefficients"])
