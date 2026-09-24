"""Console WebSocket hub (technical spec §6.3 WS row, §6.4; F15-R4).

Services call `notify(db, site_id, keys)`; the keys are queued on `session.info["after_commit"]` and broadcast as
`{"type": "invalidate", "keys": [...]}` only after the session commits, to every connected console session whose
`site_ids` include the site. A rollback discards the queue. One uvicorn worker (assumption A-15), so an in-process
hub is enough.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session, SessionTransaction
from starlette.websockets import WebSocket

log = logging.getLogger("shiftmate.ws")

AFTER_COMMIT = "after_commit"


@dataclass(eq=False)
class Connection:
    websocket: WebSocket
    site_ids: frozenset[str]
    loop: asyncio.AbstractEventLoop


class Hub:
    def __init__(self) -> None:
        self._connections: set[Connection] = set()
        self._lock = threading.Lock()

    def add(self, conn: Connection) -> None:
        with self._lock:
            self._connections.add(conn)

    def remove(self, conn: Connection) -> None:
        with self._lock:
            self._connections.discard(conn)

    def broadcast(self, site_id: str, message: dict[str, Any]) -> None:
        """Thread-safe: schedules the send on each connection's own event loop."""
        with self._lock:
            targets = [c for c in self._connections if site_id in c.site_ids]
        for conn in targets:
            asyncio.run_coroutine_threadsafe(self._send(conn, message), conn.loop)

    async def _send(self, conn: Connection, message: dict[str, Any]) -> None:
        try:
            await conn.websocket.send_json(message)
        except Exception:  # noqa: BLE001 - any send failure means a dead socket; the console reconnects
            self.remove(conn)


hub = Hub()


def notify(db: Session, site_id: str | None, keys: Iterable[str]) -> None:
    """Queues invalidation keys for `site_id`; they are sent after `db` commits."""
    keys = list(keys)
    if site_id and keys:
        db.info.setdefault(AFTER_COMMIT, []).append((site_id, keys))


def notify_message(db: Session, site_id: str, message: dict[str, Any]) -> None:
    """Queues a full message (e.g. `{"type": "sos", "sos": {...}}`) for `site_id`, sent after `db` commits."""
    db.info.setdefault(AFTER_COMMIT, []).append((site_id, message))


@event.listens_for(Session, "after_commit")
def _send_after_commit(session: Session) -> None:
    pending = session.info.pop(AFTER_COMMIT, [])
    by_site: dict[str, set[str]] = {}
    messages: list[tuple[str, dict[str, Any]]] = []
    for site_id, item in pending:
        if isinstance(item, dict):
            messages.append((site_id, item))
        else:
            by_site.setdefault(site_id, set()).update(item)
    for site_id, message in messages:
        hub.broadcast(site_id, message)
    for site_id, keys in by_site.items():
        hub.broadcast(site_id, {"type": "invalidate", "keys": sorted(keys)})


@event.listens_for(Session, "after_soft_rollback")
def _discard_on_rollback(session: Session, previous_transaction: SessionTransaction) -> None:
    # Savepoint rollbacks (one rejected push entry) keep what the rest of the batch queued.
    if not previous_transaction.nested:
        session.info.pop(AFTER_COMMIT, None)
