"""Static hosting of the built web apps (technical spec DR-07, §4.4 `static.py`).

`/console` serves the console SPA with a fallback: unknown sub-paths return `index.html` so client-side routes
load. `/app` serves the operator web export and adds `Cross-Origin-Opener-Policy: same-origin` and
`Cross-Origin-Embedder-Policy: credentialless` to every response (expo-sqlite web needs cross-origin isolation,
V-07). Each mount is skipped when its directory does not exist.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.responses import PlainTextResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Message, Receive, Scope, Send

mimetypes.add_type("application/wasm", ".wasm")  # not registered on every OS; expo-sqlite web loads a .wasm

ISOLATION_HEADERS = [
    (b"cross-origin-opener-policy", b"same-origin"),
    (b"cross-origin-embedder-policy", b"credentialless"),
]


class SPAStaticFiles(StaticFiles):
    """StaticFiles that answers unknown paths with the app's `index.html`."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
            return await super().get_response("index.html", scope)


class CrossOriginIsolated:
    """Adds the COOP/COEP headers to every HTTP response of the wrapped app."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                names = {k.lower() for k, _ in message.get("headers", [])}
                message["headers"] = list(message.get("headers", [])) + [
                    h for h in ISOLATION_HEADERS if h[0] not in names
                ]
            await send(message)

        try:
            await self.app(scope, receive, send_with_headers)
        except HTTPException as exc:  # e.g. 404: render here so the error response is isolated too
            response = PlainTextResponse(str(exc.detail), status_code=exc.status_code, headers=exc.headers)
            await response(scope, receive, send_with_headers)


def mount_static(app: FastAPI, console_dir: str | None, operator_dir: str | None) -> list[str]:
    """Mounts whichever built apps exist; returns the mounted prefixes."""
    mounted = []
    if console_dir and Path(console_dir).is_dir():
        app.mount("/console", SPAStaticFiles(directory=console_dir, html=True), name="console")
        mounted.append("/console")
    if operator_dir and Path(operator_dir).is_dir():
        app.mount(
            "/app", CrossOriginIsolated(StaticFiles(directory=operator_dir, html=True)), name="operator"
        )
        mounted.append("/app")
    return mounted
