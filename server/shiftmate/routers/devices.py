"""Device pairing, rebind and bootstrap (technical spec §6.2)."""

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from shiftmate.config import settings
from shiftmate.db import get_db
from shiftmate.errors import ShiftMateException
from shiftmate.models import (
    AuditLog,
    ChangeLog,
    Device,
    Forecast,
    Handover,
    HandoverItem,
    Machine,
    MachineProfile,
    ModelArtifact,
    Operator,
    PairingCode,
    Scenario,
    Site,
    TaskAssignment,
    Zone,
)
from shiftmate.schemas.device import (
    DeviceBootstrapResponse,
    DevicePairRequest,
    DevicePairResponse,
    DeviceRebindRequest,
    MachineWire,
    OperatorWire,
    SiteWire,
    TaskAssignmentWire,
    ZoneWire,
)
from shiftmate.security.device_auth import derive_device_secret, verify_device_auth
from shiftmate.security.ratelimit import pairing_per_ip
from shiftmate.services.machine_context import machine_context
from shiftmate.time_util import iso_ms, utc_now

router = APIRouter(prefix="/devices", tags=["devices"])


def _usable_code(db: Session, code: str, machine_id: str) -> PairingCode:
    row = db.get(PairingCode, code)
    if row is None or row.expires_at < utc_now() or row.machine_id != machine_id:
        raise ShiftMateException(status_code=404, code="pairing_code_invalid",
                                 message=f"Code not valid for {machine_id}.")
    if row.reusable and not settings.DEMO_MODE:
        # Reusable codes exist only for demos (§5.4.2): outside DEMO_MODE they are not accepted
        raise ShiftMateException(status_code=404, code="pairing_code_invalid",
                                 message="Reusable pairing codes are only valid in demo mode.")
    if not row.reusable and row.used_at is not None:
        raise ShiftMateException(status_code=409, code="pairing_code_used", message="This pairing code has already been used.")
    return row


def _pair_response(db: Session, device: Device) -> DevicePairResponse:
    ctx = machine_context(db, device.machine_id)
    return DevicePairResponse(
        device_id=device.device_id, device_secret=derive_device_secret(device.device_id), machine_id=ctx.machine_id,
        site_id=ctx.site_id, profile_id=ctx.profile_id, profile_version=ctx.profile_version, server_time=iso_ms(utc_now()),
    )


@router.post("/pair", response_model=DevicePairResponse)
def pair_device(req: DevicePairRequest, request: Request, db: Session = Depends(get_db)):
    pairing_per_ip.hit(request.client.host if request.client else "unknown")
    code_row = _usable_code(db, req.pairing_code, req.machine_id)
    if db.get(Machine, req.machine_id) is None:
        raise ShiftMateException(status_code=404, code="not_found", message=f"Machine {req.machine_id} was not found.")

    device_id = req.client_device_id or str(uuid.uuid4())
    device = db.get(Device, device_id)
    now = utc_now()
    if device is None:
        device = Device(device_id=device_id, label=req.device_label, machine_id=req.machine_id, paired_at=now,
                        last_seen_at=now)
        db.add(device)
    else:
        device.machine_id = req.machine_id
        device.label = req.device_label
        device.last_seen_at = now
        device.revoked_at = None
    if not code_row.reusable:
        code_row.used_at = now
        code_row.used_by_device_id = device_id
    db.add(AuditLog(actor=f"device:{device_id}", action="pair_device", target_type="device", target_id=device_id,
                    detail={"machine_id": req.machine_id}, created_at=now))
    db.commit()
    return _pair_response(db, device)


@router.post("/rebind", response_model=DevicePairResponse)
def rebind_device(req: DeviceRebindRequest, db: Session = Depends(get_db), device: Device = Depends(verify_device_auth)):
    code_row = _usable_code(db, req.pairing_code, req.machine_id)
    now = utc_now()
    device.machine_id = req.machine_id
    if not code_row.reusable:
        code_row.used_at = now
        code_row.used_by_device_id = device.device_id
    db.add(AuditLog(actor=f"device:{device.device_id}", action="rebind_device", target_type="device",
                    target_id=device.device_id, detail={"machine_id": req.machine_id}, created_at=now))
    db.commit()
    return _pair_response(db, device)


@router.get("/bootstrap", response_model=DeviceBootstrapResponse)
def get_bootstrap(db: Session = Depends(get_db), device: Device = Depends(verify_device_auth)):
    ctx = machine_context(db, device.machine_id)
    site = db.get(Site, ctx.site_id)
    now = utc_now()
    # "today" is the site-local date (§5.1), not the server's local date
    local_today = (now + timedelta(minutes=site.utc_offset_minutes)).date()

    classes = {(p.profile_id, p.version): p.machine_class for p in db.query(MachineProfile).all()}
    machines = db.query(Machine).filter(Machine.site_id == ctx.site_id).all()
    operators = db.query(Operator).filter(Operator.site_id == ctx.site_id).all()
    zones = db.query(Zone).filter(Zone.site_id == ctx.site_id).all()
    tasks = (
        db.query(TaskAssignment)
        .filter(TaskAssignment.machine_id == device.machine_id,
                TaskAssignment.planned_date >= local_today - timedelta(days=1),
                TaskAssignment.planned_date <= local_today + timedelta(days=1))
        .order_by(TaskAssignment.planned_date, TaskAssignment.sequence)
        .all()
    )
    latest = db.query(ChangeLog).order_by(ChangeLog.seq.desc()).first()

    handovers = []
    for ho in db.query(Handover).filter(Handover.machine_id == device.machine_id).order_by(Handover.created_at.desc()).all():
        items = db.query(HandoverItem).filter(HandoverItem.handover_id == ho.handover_id,
                                              HandoverItem.status == "open").all()
        if not items:
            continue
        handovers.append({
            "handover_id": ho.handover_id, "machine_id": ho.machine_id, "created_at": iso_ms(ho.created_at),
            "from_operator_id": ho.from_operator_id,
            "items": [{"item_id": i.item_id, "item_type": i.item_type, "text": i.text, "audiences": i.audiences,
                       "status": i.status, "task_id": i.task_id, "incident_id": i.incident_id,
                       "acknowledged_at": iso_ms(i.acknowledged_at) if i.acknowledged_at else None} for i in items],
        })

    # Forecast hours from 12 h ago to 36 h ahead (current window, not the oldest rows)
    forecast_rows = (
        db.query(Forecast)
        .filter(Forecast.site_id == ctx.site_id, Forecast.valid_to >= now - timedelta(hours=12),
                Forecast.valid_from <= now + timedelta(hours=36))
        .order_by(Forecast.valid_from.asc())
        .all()
    )

    scenarios = [s.body | {"scenario_id": s.scenario_id} for s in db.query(Scenario).filter(
        Scenario.status == "approved", Scenario.machine_class == ctx.machine_class).all()]
    artifacts = [a.body for a in db.query(ModelArtifact).filter(
        (ModelArtifact.machine_class == ctx.machine_class) | (ModelArtifact.kind == "intent")).all()]

    return DeviceBootstrapResponse(
        cursor=latest.seq if latest else 0,
        site=SiteWire(site_id=site.site_id, name=site.name, sector=site.sector, lat=site.lat, lon=site.lon,
                      utc_offset_minutes=site.utc_offset_minutes, diesel_price_inr_per_l=site.diesel_price_inr_per_l,
                      dark_start_local=site.dark_start_local, dark_end_local=site.dark_end_local,
                      job_efficiency_override=site.job_efficiency_override, congestion_level=site.congestion_level),
        zones=[ZoneWire(zone_id=z.zone_id, site_id=z.site_id, name=z.name, kind=z.kind, center_lat=z.center_lat,
                        center_lon=z.center_lon, radius_m=z.radius_m, speed_limit_kmh=z.speed_limit_kmh) for z in zones],
        machines=[MachineWire(machine_id=m.machine_id, short_id=m.short_id, site_id=m.site_id, profile_id=m.profile_id,
                              profile_version=m.profile_version,
                              machine_class=classes.get((m.profile_id, m.profile_version), "unknown"),
                              model_name=m.model_name, year_of_manufacture=m.year_of_manufacture,
                              detail_level=m.detail_level) for m in machines],
        operators=[OperatorWire(operator_id=o.operator_id, display_name=o.display_name, language=o.language,
                                skill_level=o.skill_level, experience_months=o.experience_months,
                                hired_at=o.hired_at.isoformat(), site_id=o.site_id, pin_salt=o.pin_salt,
                                pin_hash=o.pin_hash, pin_iterations=o.pin_iterations) for o in operators],
        assignments=[TaskAssignmentWire(
            task_id=t.task_id, site_id=t.site_id, machine_id=t.machine_id, task_type=t.task_type, zone_id=t.zone_id,
            location_text=t.location_text, quantity=t.quantity, unit=t.unit, material=t.material, priority=t.priority,
            completion_criterion=t.completion_criterion, planner_minutes=t.planner_minutes,
            planned_date=t.planned_date.isoformat(),
            planned_start_at=iso_ms(t.planned_start_at) if t.planned_start_at else None,
            planned_start_window_min=t.planned_start_window_min, sequence=t.sequence, source=t.source,
            revision=t.revision, status=t.status) for t in tasks],
        handovers=handovers,
        scenarios=scenarios,
        model_artifacts=artifacts,
        forecast={"site_id": ctx.site_id, "hours": [
            {"valid_from": iso_ms(f.valid_from), "valid_to": iso_ms(f.valid_to), "weather": f.weather,
             "visibility": f.visibility, "visibility_m": f.visibility_m, "temp_c": f.temp_c,
             "heat_index_c": f.heat_index_c, "wind_kmh": f.wind_kmh, "precipitation_mm": f.precipitation_mm,
             "issued_at": iso_ms(f.issued_at), "source": f.source} for f in forecast_rows]},
    )


__all__ = ["router", "datetime"]
