from fastapi import Depends, Request
from sqlalchemy.orm import Session

from shiftmate.db import get_db
from shiftmate.errors import ShiftMateException
from shiftmate.models import ConsoleSession, ConsoleUser
from shiftmate.time_util import utc_now


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> ConsoleUser:
    session_id = request.cookies.get("sm_session")
    if not session_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_id = auth_header.replace("Bearer ", "").strip()

    if not session_id:
        raise ShiftMateException(
            status_code=401,
            code="unauthenticated",
            message="No active console session found.",
        )

    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        header_val = request.headers.get("X-Requested-With")
        if header_val != "shiftmate-console":
            raise ShiftMateException(
                status_code=403,
                code="forbidden",
                message="Mutating console requests must include 'X-Requested-With: shiftmate-console'.",
            )

    sess = db.query(ConsoleSession).filter(ConsoleSession.session_id == session_id).first()
    if not sess or sess.revoked_at is not None or sess.expires_at < utc_now():
        raise ShiftMateException(
            status_code=401,
            code="unauthenticated",
            message="Console session is invalid or has expired.",
        )

    user = db.query(ConsoleUser).filter(ConsoleUser.user_id == sess.user_id).first()
    if not user or user.disabled_at is not None:
        raise ShiftMateException(
            status_code=403,
            code="forbidden",
            message="User account is disabled or not found.",
        )

    return user


def require_role(*roles: str):
    async def role_checker(user: ConsoleUser = Depends(get_current_user)) -> ConsoleUser:
        if user.role not in roles:
            raise ShiftMateException(
                status_code=403,
                code="forbidden",
                message=f"Role '{user.role}' is not authorized for this action. Required: {', '.join(roles)}",
            )
        return user

    return role_checker
