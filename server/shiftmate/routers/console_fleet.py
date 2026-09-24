"""Console fleet status (technical spec §6.3 GET /console/fleet, C6; T44 / S6). All roles read, site-scoped."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from shiftmate.db import get_db
from shiftmate.models import ConsoleUser, FleetStatus, Machine
from shiftmate.security.console_auth import get_current_user
from shiftmate.time_util import iso_ms

router = APIRouter(prefix="/console", tags=["console_fleet"])


@router.get("/fleet")
def list_fleet(
    site_id: str | None = None, db: Session = Depends(get_db), user: ConsoleUser = Depends(get_current_user)
):
    sites = [s for s in ([site_id] if site_id else (user.site_ids or [])) if s in (user.site_ids or [])]
    rows = (
        db.query(FleetStatus, Machine)
        .join(Machine, Machine.machine_id == FleetStatus.machine_id)
        .filter(Machine.site_id.in_(sites))
        .order_by(Machine.site_id, Machine.machine_id)
        .all()
    )
    return {
        "items": [
            {
                "machine_id": m.machine_id,
                "site_id": m.site_id,
                "state": f.state,
                "open_alerts": f.open_alerts,
                "last_sync_at": iso_ms(f.last_sync_at) if f.last_sync_at else None,
                "detail_level": m.detail_level,
                "data_origin": f.data_origin,
            }
            for f, m in rows
        ]
    }
