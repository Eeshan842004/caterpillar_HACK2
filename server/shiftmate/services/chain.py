"""Incident hash-chain verification (technical spec §8.10).

For each device the chained entries must be numbered 1..n without gaps; `prev_hash` must equal the previous
entry's `content_hash` (64 zeros for the first); `content_hash = sha256(prev_hash + "\\n" + canonical_payload)`;
and the stored canonical payload must describe the stored row (entry_id, kind, subtype, payload).
"""

from __future__ import annotations

import hashlib
import json

from sqlalchemy.orm import Session

from shiftmate.models import LedgerEntry

ZERO_HASH = "0" * 64


def first_bad_chain_seq(db: Session, device_id: str) -> int | None:
    """Returns the first chain_seq that fails verification (or the first missing seq), else None."""
    rows = (
        db.query(LedgerEntry)
        .filter(LedgerEntry.device_id == device_id, LedgerEntry.chain_seq.isnot(None))
        .order_by(LedgerEntry.chain_seq.asc())
        .all()
    )
    prev = ZERO_HASH
    for expected_seq, row in enumerate(rows, start=1):
        if row.chain_seq != expected_seq:
            return expected_seq
        if (row.prev_hash or "") != prev or not row.canonical_payload or not row.content_hash:
            return row.chain_seq
        recomputed = hashlib.sha256((prev + "\n" + row.canonical_payload).encode("utf-8")).hexdigest()
        if recomputed != row.content_hash:
            return row.chain_seq
        try:
            canonical = json.loads(row.canonical_payload)
        except ValueError:
            return row.chain_seq
        if (canonical.get("entry_id") != row.entry_id or canonical.get("kind") != row.kind
                or canonical.get("subtype") != row.subtype or canonical.get("payload") != row.payload):
            return row.chain_seq
        prev = row.content_hash
    return None
