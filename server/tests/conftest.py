"""Test fixtures. Tests run against an isolated temporary SQLite database (never server/var/shiftmate.db) and set
their own settings BEFORE the app is imported."""

import hashlib
import hmac
import json
import os
import tempfile
import time
import uuid
from datetime import UTC, datetime

_TMP_DIR = tempfile.mkdtemp(prefix="shiftmate-test-")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP_DIR, "test.db").replace("\\", "/")
os.environ["DEVICE_SECRET_MASTER_KEY"] = "a" * 64
os.environ["DEMO_MODE"] = "true"  # the seeded pairing codes are demo (reusable) codes
# Tests never follow a developer's .env feature switches (the live AI test turns AI on itself)
for _flag in ("AI_ENABLED", "FORECAST_ENABLED", "FLEET_SIM_ENABLED", "ISOFOREST_ENABLED"):
    os.environ[_flag] = "false"
os.environ["UPLOAD_DIR"] = os.path.join(_TMP_DIR, "uploads")
os.environ["LORA_GATEWAY_TOKEN"] = "test-gateway-token"
os.environ["SMS_CONTACTS"] = "+91 98400 11111,+91 98400 22222"

import pytest
from fastapi.testclient import TestClient

from shiftmate.db import Base, SessionLocal, engine
from shiftmate.main import app
from shiftmate.security import ratelimit
from shiftmate.security.device_auth import derive_device_secret
from shiftmate.seed import seed_database


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield


@pytest.fixture(autouse=True)
def reset_rate_limits():
    for limiter in (
        ratelimit.login_per_ip,
        ratelimit.login_per_user,
        ratelimit.pairing_per_ip,
        ratelimit.lora_per_gateway,
        ratelimit.ai_per_device,
    ):
        limiter.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def make_device_auth_headers(
    method, path, body_bytes, device_id, device_secret=None, timestamp_ms=None
) -> dict:
    device_secret = device_secret or derive_device_secret(device_id)
    timestamp_ms = timestamp_ms or int(time.time() * 1000)
    canonical = f"{method}\n{path}\n{timestamp_ms}\n{hashlib.sha256(body_bytes).hexdigest()}"
    sig = hmac.new(bytes.fromhex(device_secret), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return {"X-Device-Id": device_id, "X-Timestamp": str(timestamp_ms), "X-Signature": sig}


def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def pair(client, code="100007", machine="EX-07") -> tuple[str, str]:
    res = client.post(
        "/api/v1/devices/pair", json={"pairing_code": code, "machine_id": machine, "device_label": "test"}
    )
    assert res.status_code == 200, res.text
    return res.json()["device_id"], res.json()["device_secret"]


def entry(device_id, machine_id, kind, subtype, source, payload, audience="site", **extra) -> dict:
    ts = extra.pop("at", None) or now_iso()
    base = {
        "entry_id": str(uuid.uuid4()),
        "device_id": device_id,
        "shift_id": None,
        "machine_id": machine_id,
        "operator_id": "OP-0007",
        "kind": kind,
        "subtype": subtype,
        "source": source,
        "payload": payload,
        "observed_at": ts,
        "recorded_at": ts,
        "audience": audience,
        "data_origin": "live",
    }
    base.update(extra)
    return base


def push(client, device_id, device_secret, entries: list[dict]) -> dict:
    batch = {
        "batch": [
            {
                "entry_id": e["entry_id"],
                "type": "report",
                "created_at": e["recorded_at"],
                "body": {"kind": "ledger_entry", "entry": e},
            }
            for e in entries
        ]
    }
    body = json.dumps(batch).encode()
    headers = make_device_auth_headers("POST", "/api/v1/sync/push", body, device_id, device_secret)
    headers["Content-Type"] = "application/json"
    res = client.post("/api/v1/sync/push", content=body, headers=headers)
    assert res.status_code == 200, res.text
    return {r["entry_id"]: r for r in res.json()["results"]}


def console_login(client, username, password) -> None:
    res = client.post("/api/v1/console/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, res.text
