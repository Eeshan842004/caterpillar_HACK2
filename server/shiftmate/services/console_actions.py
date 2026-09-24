"""Shared helpers for console-side writes: server-authored ledger entries and cursors."""

from __future__ import annotations

import base64
import hashlib
import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from shiftmate.models import ConsoleUser, LedgerEntry
from shiftmate.schemas.ledger import validate_ledger_payload
from shiftmate.time_util import utc_now


def server_entry(
    db: Session,
    user: ConsoleUser,
    *,
    kind: str,
    subtype: str,
    machine_id: str,
    payload: dict[str, Any],
    audience: str,
    rule: str | None = None,
) -> LedgerEntry:
    """Appends a server-authored `reviewed` ledger entry (device_id null, author = console user), e.g.
    `incident/reviewed` and `alert/reviewed` (§5.3.2)."""
    validate_ledger_payload(kind, subtype, payload)
    now = utc_now()
    entry = LedgerEntry(
        entry_id=str(uuid.uuid4()),
        device_id=None,
        author_user_id=user.user_id,
        shift_id=None,
        machine_id=machine_id,
        operator_id=None,
        kind=kind,
        subtype=subtype,
        source="reviewed",
        payload=payload,
        observed_at=now,
        recorded_at=now,
        received_at=now,
        rule_or_model_version=rule,
        audience=audience,
        data_origin="live",
        payload_sha256=hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        review_status="ok",
    )
    db.add(entry)
    db.flush()
    return entry


def encode_cursor(values: list[Any]) -> str:
    return base64.urlsafe_b64encode(json.dumps(values, default=str).encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> list[Any]:
    padded = cursor + "=" * (-len(cursor) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
