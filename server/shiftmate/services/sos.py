"""SOS over simulated LoRaWAN (technical spec §8.19, §6.2 POST /lora/sim-uplink, T41 / S5; product F14).

Packet: 19 bytes, big-endian — version u8 (=1), machine short_id u16, event u8 (1 SOS, 2 cancel), lat×1e6 i32,
lon×1e6 i32, unix seconds u32, severity u8, seq u16. The gateway call is idempotent on (machine_id, seq). Receiving an
SOS stores `sos_events`, writes one simulated SMS per SMS_CONTACTS entry (SD-04), opens a priority-0 `sos` follow-up
and pushes `{"type": "sos", "sos": {...}}` to consoles of the site after commit. A cancel resolves the machine's
open SOS follow-ups.
"""

from __future__ import annotations

import base64
import binascii
import math
import struct
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from shiftmate.config import settings
from shiftmate.models import FollowUp, Machine, Site, SmsOutbox, SosEvent, Zone
from shiftmate.services.followups import open_group
from shiftmate.services.ws_hub import notify, notify_message
from shiftmate.time_util import iso_ms, utc_now

FORMAT = ">BHBiiIBH"
PACKET_LEN = struct.calcsize(FORMAT)  # 19
VERSION = 1
EVENTS = {1: "sos", 2: "cancel"}
EVENT_CODES = {v: k for k, v in EVENTS.items()}


class BadPacket(ValueError):
    pass


@dataclass(frozen=True)
class Packet:
    short_id: int
    event: str
    lat: float
    lon: float
    unix_s: int
    severity: int
    seq: int
    version: int = VERSION


def encode(p: Packet) -> str:
    raw = struct.pack(
        FORMAT,
        p.version,
        p.short_id,
        EVENT_CODES[p.event],
        round(p.lat * 1e6),
        round(p.lon * 1e6),
        p.unix_s,
        p.severity,
        p.seq % 65536,
    )
    return base64.b64encode(raw).decode("ascii")


def decode(packet_b64: str) -> Packet:
    try:
        raw = base64.b64decode(packet_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise BadPacket("packet is not base64") from exc
    if len(raw) != PACKET_LEN:
        raise BadPacket(f"packet must be {PACKET_LEN} bytes, got {len(raw)}")
    version, short_id, event, lat, lon, unix_s, severity, seq = struct.unpack(FORMAT, raw)
    if version != VERSION:
        raise BadPacket(f"unknown version {version}")
    if event not in EVENTS:
        raise BadPacket(f"unknown event {event}")
    return Packet(
        short_id=short_id,
        event=EVENTS[event],
        lat=lat / 1e6,
        lon=lon / 1e6,
        unix_s=unix_s,
        severity=severity,
        seq=seq,
        version=version,
    )


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def zone_at(db: Session, site_id: str, lat: float, lon: float) -> Zone | None:
    """Smallest-radius zone of the site containing the point (same rule as the device geo util)."""
    inside = [
        z
        for z in db.query(Zone).filter(Zone.site_id == site_id).all()
        if _distance_m(lat, lon, z.center_lat, z.center_lon) <= z.radius_m
    ]
    return min(inside, key=lambda z: z.radius_m) if inside else None


def _mask(number: str) -> str:
    digits = "".join(ch for ch in number if ch.isdigit())
    return "****" + digits[-4:]


def sos_wire(db: Session, ev: SosEvent) -> dict[str, Any]:
    machine = db.get(Machine, ev.machine_id)
    zone = zone_at(db, machine.site_id, ev.lat, ev.lon) if machine else None
    sms = db.query(SmsOutbox).filter(SmsOutbox.sos_id == ev.sos_id).order_by(SmsOutbox.created_at).all()
    return {
        "sos_id": ev.sos_id,
        "machine_id": ev.machine_id,
        "site_id": machine.site_id if machine else None,
        "seq": ev.seq,
        "event_type": ev.event_type,
        "lat": ev.lat,
        "lon": ev.lon,
        "zone_id": zone.zone_id if zone else None,
        "zone_name": zone.name if zone else None,
        "device_time": iso_ms(ev.device_time),
        "severity": ev.severity,
        "received_via": ev.received_via,
        "gateway_id": ev.gateway_id,
        "rssi": ev.rssi,
        "snr": ev.snr,
        "received_at": iso_ms(ev.received_at),
        "acknowledged_by": ev.acknowledged_by,
        "acknowledged_at": iso_ms(ev.acknowledged_at) if ev.acknowledged_at else None,
        "response_note": ev.response_note,
        "cancelled": is_cancelled(db, ev),
        "sms": [
            {"to_masked": s.to_masked, "body": s.body, "status": s.status, "created_at": iso_ms(s.created_at)}
            for s in sms
        ],
    }


def is_cancelled(db: Session, ev: SosEvent) -> bool:
    if ev.event_type != "sos":
        return False
    return (
        db.query(SosEvent)
        .filter(
            SosEvent.machine_id == ev.machine_id,
            SosEvent.event_type == "cancel",
            SosEvent.device_time >= ev.device_time,
        )
        .count()
        > 0
    )


def is_active(db: Session, ev: SosEvent) -> bool:
    return ev.event_type == "sos" and ev.acknowledged_at is None and not is_cancelled(db, ev)


def receive(
    db: Session,
    packet: Packet,
    *,
    via: str,
    gateway_id: str | None = None,
    rssi: int | None = None,
    snr: float | None = None,
) -> tuple[SosEvent, bool]:
    """Stores one uplink. Returns (event, created); a repeated (machine_id, seq) returns the existing event."""
    machine = db.query(Machine).filter(Machine.short_id == packet.short_id).first()
    if machine is None:
        raise BadPacket(f"unknown short_id {packet.short_id}")
    existing = (
        db.query(SosEvent)
        .filter(SosEvent.machine_id == machine.machine_id, SosEvent.seq == packet.seq)
        .first()
    )
    if existing is not None:
        return existing, False

    now = utc_now()
    ev = SosEvent(
        machine_id=machine.machine_id,
        seq=packet.seq,
        event_type=packet.event,
        lat=packet.lat,
        lon=packet.lon,
        device_time=datetime.fromtimestamp(packet.unix_s, UTC).replace(tzinfo=None),
        severity=packet.severity,
        received_via=via,
        gateway_id=gateway_id,
        rssi=rssi,
        snr=snr,
        received_at=now,
    )
    db.add(ev)
    db.flush()

    site = db.get(Site, machine.site_id)
    zone = zone_at(db, machine.site_id, packet.lat, packet.lon)
    local = ev.device_time + timedelta(minutes=site.utc_offset_minutes if site else 330)
    where = f"{zone.name} " if zone else ""
    if packet.event == "sos":
        body = (
            f"ShiftMate SOS: {machine.machine_id} at {where}({packet.lat:.5f}, {packet.lon:.5f}), "
            f"{local:%H:%M} local. Call the operator on the site radio."
        )
    else:
        body = f"ShiftMate: SOS from {machine.machine_id} cancelled by the operator at {local:%H:%M} local."
    for number in [n.strip() for n in settings.SMS_CONTACTS.split(",") if n.strip()]:
        db.add(
            SmsOutbox(
                sos_id=ev.sos_id, to_masked=_mask(number), body=body, status="simulated", created_at=now
            )
        )

    if packet.event == "sos":
        open_group(
            db,
            site_id=machine.site_id,
            category="sos",
            group_key=f"sos:{ev.sos_id}",
            title=f"SOS from {machine.machine_id}",
            summary=f"{where}({packet.lat:.5f}, {packet.lon:.5f}) — call the operator on the site radio.",
            priority=0,
            at=now,
            machine_id=machine.machine_id,
            zone_id=zone.zone_id if zone else None,
            related_id=ev.sos_id,
        )
    else:
        for fu in (
            db.query(FollowUp)
            .filter(
                FollowUp.category == "sos",
                FollowUp.machine_id == machine.machine_id,
                FollowUp.status != "resolved",
            )
            .all()
        ):
            fu.status, fu.resolved_at, fu.resolution_note, fu.updated_at = (
                "resolved",
                now,
                "Cancelled by operator",
                now,
            )
    db.flush()
    notify_message(db, machine.site_id, {"type": "sos", "sos": sos_wire(db, ev)})
    notify(db, machine.site_id, ["sos", "follow-ups"])
    return ev, True
