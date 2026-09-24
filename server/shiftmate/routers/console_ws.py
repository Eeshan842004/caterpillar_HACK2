"""Console WebSocket `/console/ws` (technical spec §6.3 WS row, §6.4).

Cookie auth at upgrade (close 4401 without a valid session); `hello` on connect; `ping` → `pong`; the hub pushes
`{"type": "invalidate", "keys": [...]}` for the user's sites after each committed change.
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from shiftmate.db import SessionLocal
from shiftmate.security.console_auth import user_for_session
from shiftmate.services.ws_hub import Connection, hub

router = APIRouter(prefix="/console", tags=["console_ws"])

UNAUTHENTICATED = 4401


@router.websocket("/ws")
async def console_ws(websocket: WebSocket) -> None:
    db = SessionLocal()
    try:
        user = user_for_session(db, websocket.cookies.get("sm_session"))
        site_ids = frozenset(user.site_ids or []) if user else frozenset()
    finally:
        db.close()

    await websocket.accept()
    if user is None:
        await websocket.close(code=UNAUTHENTICATED)
        return

    conn = Connection(websocket=websocket, site_ids=site_ids, loop=asyncio.get_running_loop())
    hub.add(conn)
    try:
        await websocket.send_json({"type": "hello"})
        while True:
            try:
                message = json.loads(await websocket.receive_text())
            except ValueError:
                continue  # ignore malformed client messages
            if isinstance(message, dict) and message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        hub.remove(conn)
