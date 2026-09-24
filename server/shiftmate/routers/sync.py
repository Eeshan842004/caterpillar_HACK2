from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from shiftmate.db import get_db
from shiftmate.models import Device
from shiftmate.schemas.sync import (
    ChangeItem,
    SyncPullResponse,
    SyncPushBatch,
    SyncPushResponse,
)
from shiftmate.security.device_auth import verify_device_auth
from shiftmate.services.changes import get_changes_for_device
from shiftmate.services.machine_context import machine_context
from shiftmate.services.projection import project_envelope
from shiftmate.time_util import utc_now, utc_now_iso

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/push", response_model=SyncPushResponse)
def push_sync(
    batch_req: SyncPushBatch,
    db: Session = Depends(get_db),
    device: Device = Depends(verify_device_auth),
):
    results = []
    for env in batch_req.batch:
        res = project_envelope(db, device, env)
        results.append(res)

    device.last_push_at = utc_now()
    db.commit()

    return SyncPushResponse(
        results=results,
        server_time=utc_now_iso(),
    )


@router.get("/pull", response_model=SyncPullResponse)
def pull_sync(
    cursor: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
    device: Device = Depends(verify_device_auth),
):
    ctx = machine_context(db, device.machine_id)
    changes, next_cursor, has_more = get_changes_for_device(
        db,
        cursor=cursor,
        limit=limit,
        machine_id=device.machine_id,
        site_id=ctx.site_id,
        machine_class=ctx.machine_class,
    )

    device.last_pull_at = utc_now()
    db.commit()

    items = [ChangeItem(**c) for c in changes]
    return SyncPullResponse(
        changes=items,
        next_cursor=next_cursor,
        has_more=has_more,
    )
