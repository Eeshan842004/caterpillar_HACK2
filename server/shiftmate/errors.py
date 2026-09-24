import secrets

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def generate_request_id() -> str:
    return "r_" + secrets.token_hex(4)


class ShiftMateException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[dict] | None = None,
        headers: dict | None = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers or {}
        super().__init__(message)


def register_error_handlers(app):
    @app.exception_handler(ShiftMateException)
    async def shiftmate_exception_handler(request: Request, exc: ShiftMateException):
        req_id = getattr(request.state, "request_id", generate_request_id())
        body = {
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": req_id,
            }
        }
        headers = dict(exc.headers)
        headers["X-Request-Id"] = req_id
        return JSONResponse(status_code=exc.status_code, content=body, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = getattr(request.state, "request_id", generate_request_id())
        details = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", []))
            msg = err.get("msg", "invalid")
            details.append({"path": loc, "issue": msg})

        body = {
            "error": {
                "code": "validation_error",
                "message": "Validation failed for request data.",
                "details": details,
                "request_id": req_id,
            }
        }
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=body,
            headers={"X-Request-Id": req_id},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        req_id = getattr(request.state, "request_id", generate_request_id())
        code_map = {
            400: "bad_request",
            401: "unauthenticated",
            403: "forbidden",
            404: "not_found",
            409: "conflict",
            413: "payload_too_large",
            422: "validation_error",
            429: "rate_limited",
            500: "internal_error",
            503: "unavailable",
        }
        code = code_map.get(exc.status_code, "error")
        body = {
            "error": {
                "code": code,
                "message": str(exc.detail),
                "details": None,
                "request_id": req_id,
            }
        }
        headers = getattr(exc, "headers", None) or {}
        headers["X-Request-Id"] = req_id
        return JSONResponse(status_code=exc.status_code, content=body, headers=headers)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        req_id = getattr(request.state, "request_id", generate_request_id())
        body = {
            "error": {
                "code": "internal_error",
                "message": "An internal server error occurred.",
                "details": None,
                "request_id": req_id,
            }
        }
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=body,
            headers={"X-Request-Id": req_id},
        )
