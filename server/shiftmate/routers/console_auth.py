import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from shiftmate.config import settings
from shiftmate.db import get_db
from shiftmate.errors import ShiftMateException
from shiftmate.models import ConsoleSession, ConsoleUser
from shiftmate.schemas.console import ConsoleLoginRequest, ConsoleUserResponse
from shiftmate.security.console_auth import get_current_user
from shiftmate.security.passwords import verify_password
from shiftmate.security.ratelimit import login_per_ip, login_per_user
from shiftmate.time_util import utc_now

router = APIRouter(prefix="/console/auth", tags=["console_auth"])


@router.post("/login", response_model=ConsoleUserResponse)
def login_console(req: ConsoleLoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    login_per_ip.hit(ip)
    login_per_user.hit(f"{ip}:{req.username}")
    user = db.query(ConsoleUser).filter(ConsoleUser.username == req.username).first()
    if not user or not verify_password(user.password_hash, req.password):
        raise ShiftMateException(
            status_code=401,
            code="invalid_credentials",
            message="Invalid username or password.",
        )

    if user.disabled_at is not None:
        raise ShiftMateException(
            status_code=403,
            code="forbidden",
            message="User account is disabled.",
        )

    session_id = secrets.token_urlsafe(32)
    expires_at = utc_now() + timedelta(hours=settings.SESSION_TTL_HOURS)

    session_row = ConsoleSession(
        session_id=session_id,
        user_id=user.user_id,
        created_at=utc_now(),
        expires_at=expires_at,
    )
    db.add(session_row)
    db.commit()

    response.set_cookie(
        key="sm_session",
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=settings.CONSOLE_COOKIE_SECURE,
        max_age=settings.SESSION_TTL_HOURS * 3600,
        path="/",
    )

    return ConsoleUserResponse(
        user_id=user.user_id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        site_ids=user.site_ids or [],
    )


@router.post("/logout", status_code=204)
def logout_console(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: ConsoleUser = Depends(get_current_user),
):
    session_id = request.cookies.get("sm_session")
    sess = db.get(ConsoleSession, session_id) if session_id else None
    if sess is not None:
        sess.revoked_at = utc_now()           # §9.1: logout revokes the session, not just the cookie
        db.commit()
    response.delete_cookie(key="sm_session", path="/")
    response.status_code = 204
    return None


@router.get("/me", response_model=ConsoleUserResponse)
def get_me(user: ConsoleUser = Depends(get_current_user)):
    return ConsoleUserResponse(
        user_id=user.user_id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        site_ids=user.site_ids or [],
    )


me_router = APIRouter(prefix="/console", tags=["console_auth"])


@me_router.get("/me", response_model=ConsoleUserResponse)
def get_me_alias(user: ConsoleUser = Depends(get_current_user)):
    """`GET /console/me` as specified in §6.3 (the /console/auth/me path is kept for compatibility)."""
    return get_me(user)
