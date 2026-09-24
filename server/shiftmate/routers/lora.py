"""Simulated LoRaWAN gateway uplink (technical spec §6.2 POST /lora/sim-uplink, §9.1; T41 / S5).

Auth: `X-Gateway-Token`, constant-time compared with LORA_GATEWAY_TOKEN; an unset token rejects every call.
"""

import hmac

from fastapi import APIRouter, Depends, Header
from pydantic import Field
from sqlalchemy.orm import Session

from shiftmate.config import settings
from shiftmate.db import get_db
from shiftmate.errors import ShiftMateException
from shiftmate.schemas.common import StrictBaseModel
from shiftmate.security.ratelimit import lora_per_gateway
from shiftmate.services import sos

router = APIRouter(prefix="/lora", tags=["lora"])


class UplinkRequest(StrictBaseModel):
    gateway_id: str = Field(min_length=1, max_length=64)
    packet_b64: str = Field(max_length=64)
    rssi: int | None = None
    snr: float | None = None
    received_at: str | None = None


class UplinkResponse(StrictBaseModel):
    ack: bool
    sos_id: str
    seq: int


@router.post("/sim-uplink", response_model=UplinkResponse)
def sim_uplink(
    req: UplinkRequest, db: Session = Depends(get_db), x_gateway_token: str | None = Header(default=None)
):
    expected = settings.LORA_GATEWAY_TOKEN or ""
    if (
        not expected
        or not x_gateway_token
        or not hmac.compare_digest(x_gateway_token.encode(), expected.encode())
    ):
        raise ShiftMateException(
            status_code=401, code="gateway_token_invalid", message="Gateway token is invalid."
        )
    lora_per_gateway.hit(req.gateway_id)
    try:
        packet = sos.decode(req.packet_b64)
        event, _ = sos.receive(
            db, packet, via="lora_sim", gateway_id=req.gateway_id, rssi=req.rssi, snr=req.snr
        )
    except sos.BadPacket as exc:
        raise ShiftMateException(status_code=400, code="bad_packet", message=str(exc)) from exc
    db.commit()
    return UplinkResponse(ack=True, sos_id=event.sos_id, seq=event.seq)
