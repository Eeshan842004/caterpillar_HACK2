"""Console WebSocket (§6.3 WS row, §6.4; TC-61): cookie auth, ping/pong, after-commit invalidation per site."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from shiftmate.main import app
from shiftmate.models import ConsoleUser
from shiftmate.security.passwords import hash_password
from tests.conftest import console_login, entry, pair, push
from tests.test_projections import _finding

WS = "/api/v1/console/ws"


def test_upgrade_without_session_closes_4401(client):
    with client.websocket_connect(WS) as ws, pytest.raises(WebSocketDisconnect) as exc:
        ws.receive_json()
    assert exc.value.code == 4401


def test_hello_and_ping_pong(client):
    console_login(client, "sup.priya", "Priya-Demo-2026")
    with client.websocket_connect(WS) as ws:
        assert ws.receive_json() == {"type": "hello"}
        ws.send_text("not json")
        ws.send_json({"type": "ping"})
        assert ws.receive_json() == {"type": "pong"}


def test_tc61_site_delay_finding_invalidates_follow_ups_after_commit(client):
    console_login(client, "sup.priya", "Priya-Demo-2026")
    device_id, secret = pair(client)
    with client.websocket_connect(WS) as ws:
        assert ws.receive_json() == {"type": "hello"}
        # A rejected entry (bad payload) is rolled back in its savepoint and must not publish anything.
        bad = entry(
            device_id, "EX-07", "inference", "finding", "inferred", {"nope": 1}, rule_or_model_version="f@1"
        )
        assert push(client, device_id, secret, [bad])[bad["entry_id"]]["status"] == "rejected"
        good = entry(
            device_id,
            "EX-07",
            "inference",
            "finding",
            "inferred",
            _finding("EX-07", "Z-CHN-LB2", "waiting_truck", 12, local_date="2026-09-01"),
            rule_or_model_version="findings@1",
        )
        assert push(client, device_id, secret, [good])[good["entry_id"]]["status"] == "confirmed"
        message = ws.receive_json()
        assert message["type"] == "invalidate" and "follow-ups" in message["keys"]


def test_other_site_session_is_not_notified(client, db):
    if db.query(ConsoleUser).filter(ConsoleUser.username == "sup.other").first() is None:
        db.add(
            ConsoleUser(
                username="sup.other",
                display_name="Other",
                role="supervisor",
                site_ids=["SITE-XYZ"],
                password_hash=hash_password("Other-Demo-2026"),
            )
        )
        db.commit()
    other = TestClient(app)
    console_login(other, "sup.other", "Other-Demo-2026")
    console_login(client, "sup.priya", "Priya-Demo-2026")
    device_id, secret = pair(client)
    with other.websocket_connect(WS) as other_ws, client.websocket_connect(WS) as ws:
        assert other_ws.receive_json() == {"type": "hello"} and ws.receive_json() == {"type": "hello"}
        finding = entry(
            device_id,
            "EX-07",
            "inference",
            "finding",
            "inferred",
            _finding("EX-07", "Z-CHN-LB2", "waiting_truck", 7, local_date="2026-09-02"),
            rule_or_model_version="findings@1",
        )
        push(client, device_id, secret, [finding])
        assert ws.receive_json()["type"] == "invalidate"
        # The other site's socket gets nothing but its own pong.
        other_ws.send_json({"type": "ping"})
        assert other_ws.receive_json() == {"type": "pong"}


def test_notify_sends_only_after_commit(db, monkeypatch):
    from sqlalchemy import text

    from shiftmate.services import ws_hub

    sent = []
    monkeypatch.setattr(ws_hub.hub, "broadcast", lambda site_id, msg: sent.append((site_id, msg)))
    db.execute(text("SELECT 1"))  # open a real transaction
    ws_hub.notify(db, "SITE-CHN-01", ["handovers"])
    db.rollback()
    assert sent == [] and ws_hub.AFTER_COMMIT not in db.info
    db.execute(text("SELECT 1"))
    ws_hub.notify(db, "SITE-CHN-01", ["tasks"])
    ws_hub.notify(db, "SITE-CHN-01", ["follow-ups", "tasks"])
    assert sent == []
    db.commit()
    assert sent == [("SITE-CHN-01", {"type": "invalidate", "keys": ["follow-ups", "tasks"]})]
