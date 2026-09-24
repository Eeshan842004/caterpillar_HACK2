from typing import Any, Literal

from pydantic import Field

from shiftmate.schemas.common import StrictBaseModel
from shiftmate.schemas.ledger import LedgerEntryWire


class OutboxEnvelopeBody(StrictBaseModel):
    kind: str  # 'ledger_entry' | 'handover_bundle'
    entry: LedgerEntryWire | None = None
    handover: dict[str, Any] | None = None
    items: list[dict[str, Any]] | None = None


class OutboxEnvelope(StrictBaseModel):
    entry_id: str
    type: str  # e.g. 'idle_reason', 'task_event', 'incident', etc.
    created_at: str
    body: OutboxEnvelopeBody


class SyncPushBatch(StrictBaseModel):
    batch: list[OutboxEnvelope] = Field(max_length=100)  # §6.2: at most 100 envelopes per push


class SyncPushResult(StrictBaseModel):
    entry_id: str
    status: Literal["confirmed", "duplicate", "needs_review", "rejected"]
    reason: str | None = None


class SyncPushResponse(StrictBaseModel):
    results: list[SyncPushResult]
    server_time: str


class ChangeItem(StrictBaseModel):
    seq: int
    change_type: str
    scope_type: str
    scope_id: str | None
    created_at: str
    payload: dict[str, Any]


class SyncPullResponse(StrictBaseModel):
    changes: list[ChangeItem]
    next_cursor: int
    has_more: bool
