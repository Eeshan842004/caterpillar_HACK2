"""SOS over simulated LoRaWAN (§8.19, §6.2 /lora/sim-uplink, §6.3 C7; TC-35, TC-58)."""

import base64
import time

import pytest

from shiftmate.models import FollowUp, SmsOutbox
from shiftmate.services import sos
from tests.conftest import console_login

URL = "/api/v1/lora/sim-uplink"
TOKEN = {"X-Gateway-Token": "test-gateway-token"}
H = {"X-Requested-With": "shiftmate-console"}
EX07 = 107  # short_id of EX-07 in the demo seed


def _packet(seq: int, event: str = "sos") -> sos.Packet:
    return sos.Packet(
        short_id=EX07, event=event, lat=12.831, lon=79.951, unix_s=int(time.time()), severity=3, seq=seq
    )


def _uplink(client, packet_b64: str, headers=TOKEN):
    return client.post(
        URL,
        json={
            "gateway_id": "GW-SIM-01",
            "packet_b64": packet_b64,
            "rssi": -97,
            "snr": 7.5,
            "received_at": "2026-09-24T10:00:00.000Z",
        },
        headers=headers,
    )


def test_tc35_codec_round_trip():
    fixture = sos.Packet(
        short_id=107, event="sos", lat=12.831002, lon=79.951234, unix_s=1790000000, severity=3, seq=12
    )
    b64 = sos.encode(fixture)
    assert len(base64.b64decode(b64)) == 19
    assert sos.decode(b64) == fixture
    assert sos.encode(sos.decode(b64)) == b64
    # Negative coordinates and seq wrap
    south = sos.Packet(short_id=1, event="cancel", lat=-33.5, lon=-70.25, unix_s=0, severity=0, seq=65535)
    assert sos.decode(sos.encode(south)) == south


def test_tc58_gateway_flow(client, db):
    console_login(client, "saf.meena", "Meena-Demo-2026")
    with client.websocket_connect("/api/v1/console/ws") as ws:
        assert ws.receive_json() == {"type": "hello"}
        res = _uplink(client, sos.encode(_packet(seq=41)))
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["ack"] is True and body["seq"] == 41

        pushed = ws.receive_json()
        assert pushed["type"] == "sos" and pushed["sos"]["sos_id"] == body["sos_id"]
        assert pushed["sos"]["zone_name"] == "Trench Area T1" and pushed["sos"]["machine_id"] == "EX-07"
        assert ws.receive_json() == {"type": "invalidate", "keys": ["follow-ups", "sos"]}

    fu = db.query(FollowUp).filter(FollowUp.group_key == f"sos:{body['sos_id']}").one()
    assert (fu.category, fu.priority, fu.status) == ("sos", 0, "open")
    sms = db.query(SmsOutbox).filter(SmsOutbox.sos_id == body["sos_id"]).all()
    assert sorted(s.to_masked for s in sms) == ["****1111", "****2222"] and all(
        s.status == "simulated" for s in sms
    )

    # Same seq again → same sos_id, no duplicates
    again = _uplink(client, sos.encode(_packet(seq=41)))
    assert again.json()["sos_id"] == body["sos_id"]
    assert db.query(SmsOutbox).filter(SmsOutbox.sos_id == body["sos_id"]).count() == 2

    # Bad token → 401; 18-byte packet → 400 bad_packet; unknown short_id → 400
    assert (
        _uplink(client, sos.encode(_packet(seq=42)), headers={"X-Gateway-Token": "nope"}).status_code == 401
    )
    assert _uplink(client, sos.encode(_packet(seq=42)), headers={}).status_code == 401
    short = base64.b64encode(base64.b64decode(sos.encode(_packet(seq=43)))[:18]).decode()
    res = _uplink(client, short)
    assert res.status_code == 400 and res.json()["error"]["code"] == "bad_packet"
    unknown = sos.Packet(short_id=65000, event="sos", lat=0, lon=0, unix_s=0, severity=3, seq=1)
    assert _uplink(client, sos.encode(unknown)).status_code == 400


def test_console_list_acknowledge_and_cancel(client, db):
    first = _uplink(client, sos.encode(_packet(seq=51))).json()["sos_id"]
    console_login(client, "sup.priya", "Priya-Demo-2026")
    active = [s["sos_id"] for s in client.get("/api/v1/console/sos").json()["items"]]
    assert first in active

    res = client.post(
        f"/api/v1/console/sos/{first}/acknowledge", json={"response_note": "Radio contact made"}, headers=H
    )
    assert res.status_code == 200 and res.json()["acknowledged_by"] is not None
    assert first not in [s["sos_id"] for s in client.get("/api/v1/console/sos").json()["items"]]
    assert first in [s["sos_id"] for s in client.get("/api/v1/console/sos?status=all").json()["items"]]
    assert db.query(FollowUp).filter(FollowUp.group_key == f"sos:{first}").one().status == "resolved"
    assert client.post(f"/api/v1/console/sos/{first}/acknowledge", json={}, headers=H).status_code == 409

    # An operator cancel resolves the machine's open SOS
    second = _uplink(client, sos.encode(_packet(seq=52))).json()["sos_id"]
    _uplink(client, sos.encode(_packet(seq=53, event="cancel")))
    assert second not in [s["sos_id"] for s in client.get("/api/v1/console/sos").json()["items"]]
    db.expire_all()
    assert db.query(FollowUp).filter(FollowUp.group_key == f"sos:{second}").one().status == "resolved"

    console_login(client, "trn.arjun", "Arjun-Demo-2026")
    assert client.get("/api/v1/console/sos").status_code == 403


@pytest.mark.parametrize("bad", ["not-base64!!", base64.b64encode(b"\x02" + b"\x00" * 18).decode()])
def test_decode_rejects_garbage_and_unknown_version(bad):
    with pytest.raises(sos.BadPacket):
        sos.decode(bad)
