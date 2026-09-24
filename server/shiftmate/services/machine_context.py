"""Machine context lookups shared by sync, bootstrap and projections.

`machine_class` comes from the machine's profile row (technical spec §5.2 `machine_profiles.machine_class`), never
from splitting the profile id: `haul_truck_90t`.split("_")[0] == "haul" was audit bug 1.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from shiftmate.errors import ShiftMateException
from shiftmate.models import Machine, MachineProfile, Site


@dataclass(frozen=True)
class MachineContext:
    machine_id: str
    site_id: str
    machine_class: str
    profile_id: str
    profile_version: int
    utc_offset_minutes: int


def machine_context(db: Session, machine_id: str) -> MachineContext:
    machine = db.get(Machine, machine_id)
    if machine is None:
        raise ShiftMateException(
            status_code=404, code="not_found", message=f"Machine {machine_id} is not registered."
        )
    profile = db.get(MachineProfile, (machine.profile_id, machine.profile_version))
    if profile is None:
        raise ShiftMateException(
            status_code=500,
            code="internal_error",
            message=f"Profile {machine.profile_id}@{machine.profile_version} is not seeded.",
        )
    site = db.get(Site, machine.site_id)
    return MachineContext(
        machine_id=machine.machine_id,
        site_id=machine.site_id,
        machine_class=profile.machine_class,
        profile_id=machine.profile_id,
        profile_version=machine.profile_version,
        utc_offset_minutes=site.utc_offset_minutes if site else 330,
    )
