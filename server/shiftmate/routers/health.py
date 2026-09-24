from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from shiftmate.config import settings
from shiftmate.db import get_db
from shiftmate.time_util import utc_now_iso

router = APIRouter()


@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    now_iso = utc_now_iso()
    content = {
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
        "version": "1.0.0",
        "server_time": now_iso,
        "ai_enabled": settings.AI_ENABLED,
        "demo_mode": settings.DEMO_MODE,
    }

    status_code = 200 if db_status == "ok" else 503
    return JSONResponse(status_code=status_code, content=content)
