"""Fleet status (T44 / S6): deterministic simulated walk, live device override, console listing."""

from sqlalchemy.orm import Session

from shiftmate.models import FleetStatus
from shiftmate.services.fleet_sim import FleetSimulator
from tests.conftest import console_login, entry, pair, push


def _snapshot(db: Session) -> list[tuple]:
    return [
        (r.machine_id, r.state, r.open_alerts) for r in db.query(FleetStatus).order_by(FleetStatus.machine_id)
    ]


def test_simulator_is_deterministic_and_moves_machines(db):
    start = _snapshot(db)
    FleetSimulator(seed=7).step(db)
    first = _snapshot(db)
    db.rollback()
    FleetSimulator(seed=7).step(db)
    assert _snapshot(db) == first != start
    db.rollback()


def test_device_push_makes_its_row_live_and_the_simulator_leaves_it(client, db):
    device_id, secret = pair(client)
    change = entry(
        device_id,
        "EX-07",
        "inference",
        "machine_state_change",
        "inferred",
        {"from": "READY", "to": "WORKING", "reason": "load"},
        rule_or_model_version="state@1",
    )
    assert push(client, device_id, secret, [change])[change["entry_id"]]["status"] == "confirmed"
    db.expire_all()
    row = db.get(FleetStatus, "EX-07")
    assert (row.state, row.data_origin) == ("WORKING", "live") and row.last_sync_at is not None

    for _ in range(20):
        FleetSimulator().step(db)
    assert (db.get(FleetStatus, "EX-07").state, db.get(FleetStatus, "EX-07").data_origin) == (
        "WORKING",
        "live",
    )
    db.rollback()


def test_console_fleet_lists_site_machines(client):
    console_login(client, "mec.dinesh", "Dinesh-Demo-2026")
    items = client.get("/api/v1/console/fleet").json()["items"]
    assert len(items) == 100
    assert {
        "machine_id",
        "site_id",
        "state",
        "open_alerts",
        "last_sync_at",
        "detail_level",
        "data_origin",
    } == set(items[0])
    one_site = client.get("/api/v1/console/fleet", params={"site_id": "SITE-CHN-01"}).json()["items"]
    assert one_site and all(i["site_id"] == "SITE-CHN-01" for i in one_site)
