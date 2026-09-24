from typing import Any

from shiftmate.schemas.common import StrictBaseModel


class DevicePairRequest(StrictBaseModel):
    pairing_code: str
    machine_id: str
    device_label: str
    client_device_id: str | None = None


class DevicePairResponse(StrictBaseModel):
    device_id: str
    device_secret: str
    machine_id: str
    site_id: str
    profile_id: str
    profile_version: int
    server_time: str


class DeviceRebindRequest(StrictBaseModel):
    machine_id: str
    pairing_code: str


class SiteWire(StrictBaseModel):
    site_id: str
    name: str
    sector: str
    lat: float
    lon: float
    utc_offset_minutes: int
    diesel_price_inr_per_l: float
    dark_start_local: str
    dark_end_local: str
    job_efficiency_override: float | None = None
    congestion_level: str


class ZoneWire(StrictBaseModel):
    zone_id: str
    site_id: str
    name: str
    kind: str
    center_lat: float
    center_lon: float
    radius_m: float
    speed_limit_kmh: float | None = None


class MachineWire(StrictBaseModel):
    machine_id: str
    short_id: int
    site_id: str
    profile_id: str
    profile_version: int
    machine_class: str
    model_name: str
    year_of_manufacture: int
    detail_level: str


class OperatorWire(StrictBaseModel):
    operator_id: str
    display_name: str
    language: str
    skill_level: str
    experience_months: int
    hired_at: str
    site_id: str
    pin_salt: str
    pin_hash: str
    pin_iterations: int


class TaskAssignmentWire(StrictBaseModel):
    task_id: str
    site_id: str
    machine_id: str | None = None
    task_type: str
    zone_id: str | None = None
    location_text: str
    quantity: float
    unit: str
    material: str
    priority: int
    completion_criterion: str
    planner_minutes: float | None = None
    planned_date: str
    planned_start_at: str | None = None
    planned_start_window_min: int = 15
    sequence: int
    source: str
    revision: int = 1
    status: str = "assigned"


class DeviceBootstrapResponse(StrictBaseModel):
    cursor: int
    site: SiteWire
    zones: list[ZoneWire]
    machines: list[MachineWire]
    operators: list[OperatorWire]
    assignments: list[TaskAssignmentWire]
    handovers: list[dict[str, Any]]
    scenarios: list[dict[str, Any]] = []
    model_artifacts: list[dict[str, Any]] = []
    forecast: dict[str, Any]
