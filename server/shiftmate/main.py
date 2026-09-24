import asyncio
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from shiftmate.config import settings
from shiftmate.db import Base, engine
from shiftmate.errors import register_error_handlers
from shiftmate.routers import (
    ai,
    console_auth,
    console_fleet,
    console_followups,
    console_incidents,
    console_operations,
    console_scenarios,
    console_sos,
    console_tasks,
    console_ws,
    devices,
    health,
    lora,
    sync,
    uploads,
)
from shiftmate.static import mount_static


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        req_id = headers.get(b"x-request-id", b"").decode("utf-8")
        if not req_id:
            req_id = "r_" + secrets.token_hex(4)

        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = req_id

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                resp_headers = list(message.get("headers", []))
                resp_headers.append((b"x-request-id", req_id.encode("utf-8")))
                message["headers"] = resp_headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


# Private-network origins (RFC 1918 + localhost), any port — e.g. the Expo web dev server on the laptop's LAN IP
LAN_ORIGIN_REGEX = (
    r"https?://(localhost|127\.0\.0\.1|10(\.\d{1,3}){3}|192\.168(\.\d{1,3}){2}"
    r"|172\.(1[6-9]|2\d|3[01])(\.\d{1,3}){2})(:\d+)?"
)


class BodySizeLimitMiddleware:
    """§6.1/§9.3: request bodies ≤ 1 MB, ≤ 1.5 MB for /uploads; larger → 413 `payload_too_large`."""

    DEFAULT_LIMIT = 1_048_576
    UPLOAD_LIMIT = 1_572_864

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        limit = self.UPLOAD_LIMIT if scope["path"].rstrip("/").endswith("/uploads") else self.DEFAULT_LIMIT
        declared = dict(scope.get("headers", [])).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > limit:
            await self._reject(scope, receive, send)
            return

        # Chunked or undeclared bodies: buffer up to the limit, then replay to the app.
        chunks, size, more = [], 0, True
        while more:
            message = await receive()
            if message["type"] != "http.request":
                break
            chunks.append(message.get("body", b""))
            size += len(chunks[-1])
            more = message.get("more_body", False)
            if size > limit:
                await self._reject(scope, receive, send)
                return
        body, sent = b"".join(chunks), False

        async def replay() -> Message:
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        await self.app(scope, replay, send)

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        req_id = scope.get("state", {}).get("request_id") or "r_" + secrets.token_hex(4)
        # X-Request-Id is added by the outer RequestIdMiddleware
        response = JSONResponse(
            status_code=413,
            content={
                "error": {
                    "code": "payload_too_large",
                    "message": "Request body is too large.",
                    "details": None,
                    "request_id": req_id,
                }
            },
        )
        await response(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Background tasks switched on by settings (single worker, A-15); all off by default and in tests."""
    tasks = []
    if settings.FORECAST_ENABLED:
        from shiftmate.services.forecast import poll_forever

        tasks.append(asyncio.create_task(poll_forever(), name="forecast-poller"))
    if settings.FLEET_SIM_ENABLED:
        from shiftmate.services.fleet_sim import run_forever

        tasks.append(asyncio.create_task(run_forever(), name="fleet-simulator"))
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        lifespan=lifespan,
        title="ShiftMate API",
        version="1.0.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        redoc_url="/redoc",
    )

    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=LAN_ORIGIN_REGEX if settings.CORS_ALLOW_LAN else None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )

    register_error_handlers(app)

    # Include routers under /api/v1
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(devices.router, prefix="/api/v1")
    app.include_router(sync.router, prefix="/api/v1")
    app.include_router(console_auth.router, prefix="/api/v1")
    app.include_router(console_followups.router, prefix="/api/v1")
    app.include_router(console_incidents.router, prefix="/api/v1")
    app.include_router(console_operations.router, prefix="/api/v1")
    app.include_router(console_scenarios.router, prefix="/api/v1")
    app.include_router(console_tasks.router, prefix="/api/v1")
    app.include_router(console_fleet.router, prefix="/api/v1")
    app.include_router(console_sos.router, prefix="/api/v1")
    app.include_router(lora.router, prefix="/api/v1")
    app.include_router(ai.router, prefix="/api/v1")
    app.include_router(uploads.router, prefix="/api/v1")
    app.include_router(console_auth.me_router, prefix="/api/v1")
    app.include_router(console_ws.router, prefix="/api/v1")

    # Also mount health on root /health
    app.include_router(health.router)

    # Built web apps on the same origin (DR-07); skipped when not built
    mount_static(app, settings.STATIC_CONSOLE_DIR, settings.STATIC_OPERATOR_DIR)

    from fastapi.responses import RedirectResponse

    @app.get("/api/docs", include_in_schema=False)
    async def redirect_api_docs():
        return RedirectResponse(url="/docs")

    @app.get("/", include_in_schema=False)
    async def redirect_root():
        return RedirectResponse(url="/docs")

    return app


app = create_app()
