import hashlib
import hmac
import time

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from shiftmate.config import settings
from shiftmate.db import get_db
from shiftmate.errors import ThroughlineException
from shiftmate.models import Device
from shiftmate.time_util import utc_now


def derive_device_secret(device_id: str) -> str:
    master_key = bytes.fromhex(settings.DEVICE_SECRET_MASTER_KEY)
    return hmac.new(master_key, device_id.encode("utf-8"), hashlib.sha256).hexdigest()


async def verify_device_auth(request: Request, db: Session = Depends(get_db)) -> Device:
    device_id = request.headers.get("X-Device-Id")
    timestamp_str = request.headers.get("X-Timestamp")
    signature = request.headers.get("X-Signature")

    if not device_id or not timestamp_str or not signature:
        raise ThroughlineException(
            status_code=401,
            code="unauthenticated",
            message="Missing device authentication headers (X-Device-Id, X-Timestamp, X-Signature).",
        )

    try:
        req_ts = int(timestamp_str)
    except ValueError:
        raise ThroughlineException(
            status_code=401,
            code="unauthenticated",
            message="Invalid X-Timestamp header format.",
        )

    now_ms = int(time.time() * 1000)
    if abs(now_ms - req_ts) > 300000:
        raise ThroughlineException(
            status_code=401,
            code="timestamp_skew",
            message="Request timestamp is outside the allowed skew window (+/- 300 s).",
        )

    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise ThroughlineException(
            status_code=401,
            code="device_unknown",
            message="Device is not recognized on this server.",
        )

    if device.revoked_at is not None:
        raise ThroughlineException(
            status_code=401,
            code="device_revoked",
            message="Device pairing has been revoked.",
        )

    body_bytes = await request.body()
    body_sha256 = hashlib.sha256(body_bytes).hexdigest()

    url_path = request.url.path
    if request.url.query:
        url_path += f"?{request.url.query}"

    canonical = f"{request.method}\n{url_path}\n{timestamp_str}\n{body_sha256}"
    device_secret = derive_device_secret(device_id)
    secret_bytes = bytes.fromhex(device_secret)
    expected_sig = hmac.new(secret_bytes, canonical.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature.lower(), expected_sig.lower()):
        raise ThroughlineException(
            status_code=401,
            code="signature_invalid",
            message="Device HMAC signature is invalid.",
        )

    device.last_seen_at = utc_now()
    db.commit()
    return device
