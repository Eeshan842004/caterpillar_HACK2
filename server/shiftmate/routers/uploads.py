"""Voice-note / site-tip uploads (technical spec §6.2 POST /uploads, §5.5 Uploads, §9.5; TC-59) and the
console playback endpoint GET /console/uploads/{upload_id} (§6.3).

Base64 JSON, decoded size ≤ 1 048 576 bytes (413 above), content types audio/mp4 or audio/webm, idempotent by
`entry_id`. Storage keys are server-generated: `voice_notes/<yyyy>/<mm>/<upload_id>.<m4a|webm>` under UPLOAD_DIR
(`site_tips/...` for site tips).
"""

import base64
import binascii
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from shiftmate.config import settings
from shiftmate.db import get_db
from shiftmate.errors import ShiftMateException
from shiftmate.models import ConsoleUser, Device, Machine, Upload
from shiftmate.schemas.device import UploadRequest, UploadResponse
from shiftmate.security.console_auth import get_current_user
from shiftmate.security.device_auth import verify_device_auth
from shiftmate.time_util import utc_now

MAX_UPLOAD_BYTES = 1_048_576
EXTENSIONS = {"audio/mp4": "m4a", "audio/webm": "webm"}
FOLDERS = {"voice_note": "voice_notes", "site_tip": "site_tips"}

router = APIRouter(tags=["uploads"])


def _response(u: Upload) -> UploadResponse:
    return UploadResponse(upload_id=u.upload_id, storage_key=u.storage_key, size_bytes=u.size_bytes)


@router.post("/uploads", response_model=UploadResponse)
def upload(req: UploadRequest, db: Session = Depends(get_db), device: Device = Depends(verify_device_auth)):
    existing = db.query(Upload).filter(Upload.entry_id == req.entry_id).first()
    if existing is not None:
        if existing.device_id != device.device_id:
            raise ShiftMateException(
                status_code=409, code="conflict", message="entry_id belongs to another device."
            )
        return _response(existing)
    try:
        data = base64.b64decode(req.data_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ShiftMateException(
            status_code=422, code="validation_error", message="data_b64 is not base64."
        ) from exc
    if len(data) > MAX_UPLOAD_BYTES:
        raise ShiftMateException(status_code=413, code="payload_too_large", message="Upload exceeds 1 MB.")
    if not data:
        raise ShiftMateException(status_code=422, code="validation_error", message="Upload is empty.")

    upload_id, now = str(uuid.uuid4()), utc_now()
    key = f"{FOLDERS[req.kind]}/{now:%Y}/{now:%m}/{upload_id}.{EXTENSIONS[req.content_type]}"
    path = settings.upload_path / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    row = Upload(
        upload_id=upload_id,
        entry_id=req.entry_id,
        device_id=device.device_id,
        kind=req.kind,
        content_type=req.content_type,
        size_bytes=len(data),
        storage_key=key,
        created_at=now,
    )
    db.add(row)
    db.commit()
    return _response(row)


@router.get("/console/uploads/{upload_id}")
def play_upload(upload_id: str, db: Session = Depends(get_db), user: ConsoleUser = Depends(get_current_user)):
    row = db.get(Upload, upload_id)
    device = db.get(Device, row.device_id) if row else None
    machine = db.get(Machine, device.machine_id) if device else None
    path = settings.upload_path / row.storage_key if row else None
    if row is None or machine is None or machine.site_id not in (user.site_ids or []) or not path.is_file():
        raise ShiftMateException(status_code=404, code="not_found", message="Upload not found.")
    return FileResponse(path, media_type=row.content_type, headers={"X-Content-Type-Options": "nosniff"})
