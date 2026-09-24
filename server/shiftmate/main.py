import secrets

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from shiftmate.config import settings
from shiftmate.db import Base, engine
from shiftmate.errors import register_error_handlers
from shiftmate.routers import (
    console_auth,
    console_followups,
    console_incidents,
    console_operations,
    devices,
    health,
    sync,
)


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


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="Throughline API",
        version="1.0.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        redoc_url="/redoc",
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
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
    app.include_router(console_auth.me_router, prefix="/api/v1")

    # Also mount health on root /health
    app.include_router(health.router)

    from fastapi.responses import RedirectResponse

    @app.get("/api/docs", include_in_schema=False)
    async def redirect_api_docs():
        return RedirectResponse(url="/docs")

    @app.get("/", include_in_schema=False)
    async def redirect_root():
        return RedirectResponse(url="/docs")

    return app


app = create_app()
