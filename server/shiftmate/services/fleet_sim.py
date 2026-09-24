"""Fleet status (technical spec T44 / S6): a simulated fleet of 100 machines plus live overrides from devices.

When FLEET_SIM_ENABLED, a background task random-walks machine states and open-alert counts every 5 s from a fixed
seed, marking rows `data_origin = 'synthetic'` (shown as "simulated" in C6). A paired device's pushes overwrite its
own machine's row (`data_origin = 'live'`), and the simulator never touches live rows again. Each change sends a
`fleet` invalidation to consoles of that site.
"""

from __future__ import annotations

import asyncio
import random

from sqlalchemy.orm import Session

from shiftmate.db import SessionLocal
from shiftmate.models import FleetStatus, LedgerEntry, Machine
from shiftmate.services.ws_hub import notify
from shiftmate.time_util import utc_now

SEED = 20260923
TICK_S = 5
CHANGE_PROB = 0.25  # chance a machine changes state on a tick
# Plausible next states (weights) from each state
TRANSITIONS: dict[str, list[tuple[str, int]]] = {
    "OFF": [("READY", 1)],
    "SECURED": [("READY", 3), ("OFF", 1)],
    "READY": [("WORKING", 4), ("TRAVELLING", 2), ("SECURED", 2)],
    "WORKING": [("READY", 2), ("TRAVELLING", 2), ("SECURED", 1)],
    "TRAVELLING": [("WORKING", 3), ("READY", 2)],
    "UNKNOWN": [("READY", 1)],
}


class FleetSimulator:
    def __init__(self, seed: int = SEED) -> None:
        self.rng = random.Random(seed)

    def step(self, db: Session) -> set[str]:
        """One tick over every non-live row (stable order, so a seed gives the same walk). Returns changed sites."""
        now, changed = utc_now(), set()
        rows = (
            db.query(FleetStatus, Machine.site_id)
            .join(Machine, Machine.machine_id == FleetStatus.machine_id)
            .filter(FleetStatus.data_origin != "live")
            .order_by(FleetStatus.machine_id)
            .all()
        )
        for row, site_id in rows:
            moved = self.rng.random() < CHANGE_PROB
            if moved:
                options = TRANSITIONS.get(row.state, TRANSITIONS["UNKNOWN"])
                row.state = self.rng.choices([s for s, _ in options], weights=[w for _, w in options])[0]
            if row.state in ("WORKING", "TRAVELLING") and self.rng.random() < 0.03:
                row.open_alerts += 1
            elif row.open_alerts and self.rng.random() < 0.2:
                row.open_alerts -= 1
            if moved or self.rng.random() < 0.5:
                row.last_sync_at = now
            row.updated_at, row.data_origin = now, "synthetic"
            changed.add(site_id)
        for site_id in changed:
            notify(db, site_id, ["fleet"])
        return changed

    def tick(self) -> None:
        db = SessionLocal()
        try:
            self.step(db)
            db.commit()
        finally:
            db.close()


async def run_forever() -> None:
    sim = FleetSimulator()
    while True:
        await asyncio.to_thread(sim.tick)
        await asyncio.sleep(TICK_S)


def apply_device_entry(db: Session, row: LedgerEntry) -> bool:
    """A real device's push overwrites its own machine's fleet row. Returns True when the console-visible state,
    alert count or live status changed (the sync time alone does not warrant a `fleet` invalidation)."""
    fleet = db.get(FleetStatus, row.machine_id)
    if fleet is None:
        fleet = FleetStatus(
            machine_id=row.machine_id, state="UNKNOWN", open_alerts=0, data_origin="synthetic"
        )
        db.add(fleet)
    before = (fleet.state, fleet.open_alerts, fleet.data_origin)
    if row.kind == "inference" and row.subtype == "machine_state_change":
        fleet.state = row.payload.get("to") or fleet.state
    elif row.kind == "alert" and row.subtype == "raised":
        fleet.open_alerts = (fleet.open_alerts or 0) + 1
    elif row.kind == "alert" and row.subtype == "cleared":
        fleet.open_alerts = max(0, (fleet.open_alerts or 0) - 1)
    now = utc_now()
    fleet.last_sync_at, fleet.updated_at, fleet.data_origin = now, now, "live"
    return (fleet.state, fleet.open_alerts, fleet.data_origin) != before
