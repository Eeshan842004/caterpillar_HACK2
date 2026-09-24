"""Operational timeline for the synthetic dataset (technical spec §8.22, DATASET_SCHEMA §4–§5).

Builds shifts, tasks, idle intervals, alerts, incidents, 5-minute summaries and the canonical ledger.
Every ledger payload follows technical spec §5.3.2 (checked by `validate.py` against the server's
payload registry); flat CSV rows are projections of those ledger entries.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from datetime import date as date_cls
from typing import Any

import numpy as np

from shiftmate_ml.datagen.effects import compute_baseline_minutes, compute_task_effects, sample_task_noise

SITE_DELAY_REASONS = {
    "waiting_truck",
    "waiting_loader",
    "shovel_queue",
    "crusher_queue",
    "access_blocked",
    "instructed_hold",
}
PLACES = ["front", "front_right", "right", "rear_right", "rear", "rear_left", "left", "front_left"]
IDLE_THRESHOLD_S = 300
DEMO_RAVI, DEMO_KUMAR, DEMO_SENTHIL = "OP-0007", "OP-0011", "OP-0021"

# Zone used for each (site, task type); falls back to the site's first zone
TASK_ZONES = {
    ("SITE-CHN-01", "trenching"): ["Z-CHN-TR1", "Z-CHN-TR2"],
    ("SITE-CHN-01", "truck_loading"): ["Z-CHN-LB2"],
    ("SITE-CHN-01", "backfilling"): ["Z-CHN-TR1", "Z-CHN-TR2"],
    ("SITE-CHN-01", "grading"): ["Z-CHN-YARD"],
    ("SITE-CHN-01", "pipe_lifting"): ["Z-CHN-TR2"],
    ("SITE-BLR-02", "grading"): ["Z-BLR-YARD"],
    ("SITE-MIN-03", "truck_loading"): ["Z-MIN-SH1"],
    ("SITE-MIN-03", "haul_overburden"): ["Z-MIN-R3", "Z-MIN-R1"],
    ("SITE-MIN-03", "haul_ore"): ["Z-MIN-R3", "Z-MIN-R1"],
    ("SITE-MIN-04", "haul_overburden"): ["Z-MIN4-R1"],
    ("SITE-MIN-04", "haul_ore"): ["Z-MIN4-R1"],
}
SITE_DEFAULT_ZONE = {
    "SITE-CHN-01": "Z-CHN-TR1",
    "SITE-BLR-02": "Z-BLR-TR1",
    "SITE-MIN-03": "Z-MIN-YARD",
    "SITE-MIN-04": "Z-MIN4-R1",
}

LESSONS = {
    "excavator": [
        "ex-l-belt-lockout",
        "ex-l-swing-radius",
        "ex-l-truck-loading",
        "ex-s-person-swing",
        "ex-s-truck-queue",
    ],
    "haul_truck": ["ht-l-haul-speed", "ht-l-light-vehicles", "ht-l-queue-discipline", "ht-s-pickup-dust"],
}


# ----------------------------------------------------------------------------- helpers


def iso_utc(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def epoch_ms(dt: datetime) -> int:
    return round(dt.timestamp() * 1000)


def canonical_json(value: Any) -> str:
    """§8.10 canonical JSON: sorted keys, no whitespace, non-ASCII kept (matches JSON.stringify)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def parse_hhmm(text: str) -> int:
    h, m = text.split(":")
    return int(h) * 60 + int(m)


def visibility_band(vis_m: float | None, darkness: bool) -> str:
    """§8.6.2: ≥ 5 000 m good, 1 000–5 000 moderate, < 1 000 poor; darkness raises good to moderate."""
    if vis_m is None or vis_m >= 5000:
        band = "good"
    elif vis_m >= 1000:
        band = "moderate"
    else:
        band = "poor"
    if darkness and band == "good":
        band = "moderate"
    return band


def temperature_band(temp_c: float | None) -> str:
    """§8.6.2: < 20 cool, 20–30 mild, 30–38 hot, > 38 extreme; missing → mild."""
    if temp_c is None:
        return "mild"
    if temp_c < 20:
        return "cool"
    if temp_c < 30:
        return "mild"
    if temp_c <= 38:
        return "hot"
    return "extreme"


def derive_weather(cond: dict[str, Any]) -> str:
    """§8.6.2 weather feature from a forecast hour: rain > dust > fog > wind > clear."""
    if cond["weather"] == "rain" or float(cond["precipitation_mm"]) >= 0.5:
        return "rain"
    if cond["weather"] == "dusty":
        return "dusty"
    if cond.get("visibility_m") is not None and float(cond["visibility_m"]) < 1000:
        return "foggy"
    if float(cond["wind_kmh"]) >= 38:
        return "windy"
    return "clear"


def time_of_day(local_hour: int) -> str:
    if 6 <= local_hour < 12:
        return "morning"
    if 12 <= local_hour < 18:
        return "afternoon"
    if 18 <= local_hour < 22:
        return "evening"
    return "night"


def is_dark(local_dt: datetime, site: dict[str, Any]) -> bool:
    minute = local_dt.hour * 60 + local_dt.minute
    start = parse_hhmm(site.get("dark_start_local", "19:00"))
    end = parse_hhmm(site.get("dark_end_local", "06:00"))
    return minute >= start or minute < end if start > end else start <= minute < end


def months_between(start: date_cls, end: date_cls) -> int:
    """Whole months from `start` to `end` (0 if end is earlier)."""
    if end < start:
        return 0
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return max(0, months)


@dataclass
class Interval:
    kind: str  # idle | pause | block
    start: datetime
    end: datetime
    idle_class: str | None = None
    category: str | None = None


@dataclass
class ShiftState:
    open_handover_items: list[dict[str, Any]] = field(default_factory=list)
    last_operator: str | None = None


# ----------------------------------------------------------------------------- builder


class TimelineBuilder:
    def __init__(self, gen: Any, conditions_map: dict[str, dict[str, Any]]):
        self.gen = gen
        self.cfg = gen.config
        self.raw = gen.config.raw
        self.rng: np.random.Generator = gen.rng
        self.conditions_map = conditions_map
        self.sites = {s["site_id"]: s for s in gen.sites}
        self.origin = gen.config.data_origin
        self.scale = gen.effect_scale

        self.shifts: list[dict[str, Any]] = []
        self.tasks: list[dict[str, Any]] = []
        self.idles: list[dict[str, Any]] = []
        self.alerts: list[dict[str, Any]] = []
        self.summaries: list[dict[str, Any]] = []
        self.ledger: list[dict[str, Any]] = []

        self.chains: dict[str, dict[str, Any]] = {}  # per device: {seq, prev_hash}
        self.forecast_logged: set = set()
        self.machine_state: dict[str, ShiftState] = {}
        self.ravi_trenching_done = False

        held = self.cfg.split_policy.get("unseen_operator", {})
        self.held_out = set(held.get("held_out_excavators", []) + held.get("held_out_haul_trucks", []))
        self.operators = {o["operator_id"]: o for o in gen.operators}
        self.machine_ops = self._assign_machine_operators()

    # ------------------------------------------------------------------ ids / ledger

    def uid(self, tag: str) -> str:
        from shiftmate_ml.datagen.generate import deterministic_uuid

        return deterministic_uuid(self.rng, tag)

    def ledger_entry(
        self,
        dev_id: str,
        shift_id: str | None,
        machine_id: str,
        operator_id: str | None,
        kind: str,
        subtype: str,
        source: str,
        payload: dict[str, Any],
        observed_at: datetime,
        audience: str,
        *,
        entry_id: str | None = None,
        rule: str | None = None,
        recorded_at: datetime | None = None,
        supersedes: str | None = None,
        original_text: str | None = None,
        confidence: str | None = None,
        freshness_s: float | None = None,
    ) -> dict[str, Any]:
        eid = entry_id or self.uid(f"ledger:{kind}:{subtype}")
        observed_at = observed_at.replace(microsecond=observed_at.microsecond // 1000 * 1000)
        rec_at = recorded_at or observed_at
        rec_at = rec_at.replace(microsecond=rec_at.microsecond // 1000 * 1000)
        entry: dict[str, Any] = {
            "entry_id": eid,
            "device_id": dev_id,
            "shift_id": shift_id,
            "machine_id": machine_id,
            "operator_id": operator_id,
            "kind": kind,
            "subtype": subtype,
            "source": source,
            "payload": payload,
            "observed_at": iso_utc(observed_at),
            "recorded_at": iso_utc(rec_at),
            "freshness_s": freshness_s,
            "confidence": confidence,
            "rule_or_model_version": rule,
            "original_text": original_text,
            "supersedes": supersedes,
            "audience": audience,
            "data_origin": self.origin,
            "sync_status": "confirmed",
            "chain_seq": None,
            "prev_hash": None,
            "content_hash": None,
            "canonical_payload": None,
        }
        if self._is_chain_member(kind, subtype, payload):
            chain = self.chains.setdefault(dev_id, {"seq": 0, "prev_hash": "0" * 64})
            chain["seq"] += 1
            canonical = canonical_json(
                {
                    "entry_id": eid,
                    "device_id": dev_id,
                    "shift_id": shift_id,
                    "machine_id": machine_id,
                    "operator_id": operator_id,
                    "kind": kind,
                    "subtype": subtype,
                    "source": source,
                    "payload": payload,
                    "observed_at": epoch_ms(observed_at),
                    "recorded_at": epoch_ms(rec_at),
                    "supersedes": supersedes,
                    "original_text": original_text,
                }
            )
            content_hash = hashlib.sha256((chain["prev_hash"] + "\n" + canonical).encode("utf-8")).hexdigest()
            entry.update(
                chain_seq=chain["seq"],
                prev_hash=chain["prev_hash"],
                content_hash=content_hash,
                canonical_payload=canonical,
            )
            chain["prev_hash"] = content_hash
        self.ledger.append(entry)
        return entry

    @staticmethod
    def _is_chain_member(kind: str, subtype: str, payload: dict[str, Any]) -> bool:
        """§8.10 chain members: incident entries, incident reports/extractions and corrections of those."""
        if kind == "incident":
            return True
        if (kind, subtype) in {("report", "incident_report"), ("inference", "incident_extraction")}:
            return True
        return kind == "correction" and subtype in {"incident_report", "incident_extraction"}

    # ------------------------------------------------------------------ roster

    def _assign_machine_operators(self) -> dict[str, list[str]]:
        """Each machine gets 2–3 regular operators from the same site and class (round robin)."""
        by_pool: dict[tuple[str, str], list[str]] = {}
        for o in sorted(self.gen.operators, key=lambda x: x["operator_id"]):
            by_pool.setdefault((o["site_id"], o["regular_machine_class"]), []).append(o["operator_id"])
        machines_by_pool: dict[tuple[str, str], list[str]] = {}
        for m in sorted(self.gen.operational_machines, key=lambda x: x["machine_id"]):
            machines_by_pool.setdefault((m["site_id"], m["machine_class"]), []).append(m["machine_id"])

        result: dict[str, list[str]] = {}
        for pool, mids in machines_by_pool.items():
            ops = by_pool.get(pool, [])
            if not ops:
                raise ValueError(f"No operators for {pool}; fix the demo seed roster")
            for i, mid in enumerate(mids):
                result[mid] = [ops[j] for j in range(i, len(ops), len(mids))] or [ops[i % len(ops)]]

        def pin(machine_id: str, op_id: str) -> None:
            if op_id in result[machine_id]:
                return
            for ops in result.values():
                if op_id in ops:
                    donor = result[machine_id][0]
                    ops[ops.index(op_id)] = donor
                    result[machine_id][0] = op_id
                    return

        pin("EX-07", DEMO_KUMAR)
        pin("EX-07", DEMO_RAVI)
        pin("HT-03", DEMO_SENTHIL)
        return result

    def _operator_for_day(self, machine: dict[str, Any], day: datetime, day_idx: int) -> str | None:
        hired = [
            op
            for op in self.machine_ops[machine["machine_id"]]
            if date_cls.fromisoformat(self.operators[op]["hired_at"]) <= day.date()
        ]
        if not hired:
            return None
        op = hired[day_idx % len(hired)]
        if op == DEMO_RAVI and not self._ravi_can_work(machine, day):
            others = [o for o in hired if o != DEMO_RAVI]
            op = others[0] if others else None
        return op

    def _ravi_can_work(self, machine: dict[str, Any], day: datetime) -> bool:
        """Demo constraint (tech §5.4.2): Ravi never starts a task in rain, dust or darkness.

        He only works day shifts, and only on days whose 06:00–13:00 forecast is free of rain and dust.
        """
        site = self.sites[machine["site_id"]]
        for hour in range(6, 13):
            cond = self._condition_at_local(site, day, hour)
            if cond and derive_weather(cond) in ("rain", "dusty"):
                return False
        return True

    # ------------------------------------------------------------------ conditions

    def _condition_at_local(
        self, site: dict[str, Any], day: datetime, local_hour: int
    ) -> dict[str, Any] | None:
        local = datetime(day.year, day.month, day.day, local_hour, tzinfo=UTC)
        return self.conditions_map.get(
            f"{site['site_id']}:{iso_utc(local - timedelta(minutes=site['utc_offset_minutes']))}"
        )

    def condition_at(self, site: dict[str, Any], when_utc: datetime) -> dict[str, Any] | None:
        """Forecast hour covering `when_utc`. Forecast hours are aligned to SITE-LOCAL hours
        (at +5:30 they start at :30 UTC), so floor in local time, not UTC (audit bug D1)."""
        offset = timedelta(minutes=site["utc_offset_minutes"])
        local = (when_utc + offset).replace(minute=0, second=0, microsecond=0)
        return self.conditions_map.get(f"{site['site_id']}:{iso_utc(local - offset)}")

    # ------------------------------------------------------------------ main loop

    def build(self) -> dict[str, list[dict[str, Any]]]:
        for day_idx, day in enumerate(self.gen.working_dates):
            week = day_idx // self.cfg.working_days_per_week + 1
            for machine in self.gen.operational_machines:
                op_id = self._operator_for_day(machine, day, day_idx)
                if op_id is None:
                    continue
                self._build_shift(machine, op_id, day, day_idx, week)
        return {
            "shifts": self.shifts,
            "tasks": self.tasks,
            "idle_events": self.idles,
            "alerts": self.alerts,
            "summaries_5m": self.summaries,
            "ledger_entries": self.ledger,
        }

    # ------------------------------------------------------------------ shift

    def _build_shift(self, m: dict[str, Any], op_id: str, day: datetime, day_idx: int, week: int) -> None:
        mid, mclass, site_id = m["machine_id"], m["machine_class"], m["site_id"]
        site = self.sites[site_id]
        offset = timedelta(minutes=site["utc_offset_minutes"])
        profile = self.gen.profiles[m["profile_id"]]
        dev_id = self.gen.device_ids[mid]
        op = self.operators[op_id]
        state = self.machine_state.setdefault(mid, ShiftState())

        if site["sector"] == "mining":
            code_idx = (day_idx + int(m["short_id"])) % 3
        else:
            code_idx = (day_idx + int(m["short_id"])) % 2
        if op_id == DEMO_RAVI:
            code_idx = 0
        shift_code = ["day", "evening", "night"][code_idx]
        start_hour = [6, 14, 22][code_idx]
        shift_start = datetime(day.year, day.month, day.day, start_hour, tzinfo=UTC) - offset
        shift_id = self.uid(f"shift:{mid}:{day_idx}")
        handover_id = self.uid(f"handover:{mid}:{day_idx}")
        hired = date_cls.fromisoformat(op["hired_at"])
        exp_months = months_between(hired, day.date())

        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "shift_event",
            "start",
            "reported",
            {
                "auth_method": "pin",
                "language": op["language"],
                "guidance": "guided" if (day.date() - hired).days < 30 else "concise",
                "profile_id": m["profile_id"],
                "profile_version": int(m.get("profile_version", 1)),
            },
            shift_start,
            "site",
        )
        # Incoming operator acknowledges open handover items (acknowledged ≠ resolved)
        if state.open_handover_items and state.last_operator != op_id:
            for item in state.open_handover_items:
                self.ledger_entry(
                    dev_id,
                    shift_id,
                    mid,
                    op_id,
                    "handover_item",
                    "acknowledged",
                    "reported",
                    {"item_id": item["item_id"]},
                    shift_start + timedelta(minutes=3),
                    "next_operator",
                )
            state.open_handover_items = []

        cursor = shift_start + timedelta(minutes=10)
        # Cold-start warm-up (required idle)
        req = self.raw.get("required_idle", {})
        if self.rng.random() < req.get("warmup_prob", 0.0):
            dur = int(req.get("warmup_s", 420) + self.rng.integers(-60, 61))
            self._required_idle(
                dev_id,
                shift_id,
                m,
                op_id,
                site,
                None,
                SITE_DEFAULT_ZONE[site_id],
                cursor,
                dur,
                basis="warmup",
            )
            cursor += timedelta(seconds=dur + 120)
        else:
            cursor += timedelta(minutes=5)

        last_end = cursor
        for seq in (1, 2):
            result = self._build_task(
                m, profile, site, op, exp_months, dev_id, shift_id, day, week, seq, cursor
            )
            if result is None:
                continue
            task_end, heavy, zone = result
            last_end = task_end
            cursor = task_end + timedelta(minutes=float(self.rng.uniform(10, 25)))
            if heavy and self.rng.random() < req.get("cooldown_prob", 0.0):
                dur = int(req.get("cooldown_s", 300) + self.rng.integers(0, 90))
                self._required_idle(
                    dev_id,
                    shift_id,
                    m,
                    op_id,
                    site,
                    None,
                    zone,
                    task_end + timedelta(seconds=20),
                    dur,
                    basis="cooldown",
                )
                cursor = max(cursor, task_end + timedelta(seconds=dur + 60))
                last_end = max(last_end, task_end + timedelta(seconds=dur + 20))

        shift_end = max(shift_start + timedelta(hours=8), last_end + timedelta(minutes=15))

        # Private learning (operator_only, device history only)
        if op["skill_level"] != "expert" and self.rng.random() < 0.08:
            self._learning(dev_id, shift_id, mid, op_id, mclass, last_end + timedelta(minutes=5))

        # Handover note for the next operator (open until a console role resolves it)
        handover_ref: str | None = None
        if self.rng.random() < 0.15:
            handover_ref = handover_id
            item_id = self.uid(f"hitem:{handover_id}")
            text = str(
                self.rng.choice(
                    [
                        "Soft ground near the east edge — keep the tracks back.",
                        "Loading bay access gets congested after lunch.",
                        "Hydraulic temperature ran warm in the afternoon — watch the gauge.",
                        "Haul road dusty near the crusher turn — lights on.",
                    ]
                )
            )
            t = shift_end - timedelta(minutes=8)
            note = self.ledger_entry(
                dev_id,
                shift_id,
                mid,
                op_id,
                "report",
                "handover_note",
                "reported",
                {"handover_id": handover_id, "item_id": item_id, "text": text, "via": "button"},
                t,
                "next_operator",
            )
            self.ledger_entry(
                dev_id,
                shift_id,
                mid,
                op_id,
                "handover_item",
                "added",
                "reported",
                {
                    "handover_id": handover_id,
                    "item_id": item_id,
                    "item_type": "note",
                    "text_key": None,
                    "text_params": None,
                    "text": text,
                    "audiences": ["next_operator"],
                    "source_entry_ids": [note["entry_id"]],
                    "task_id": None,
                    "incident_id": None,
                    "carried_from_item_id": None,
                },
                t + timedelta(seconds=30),
                "next_operator",
            )
            state.open_handover_items.append({"item_id": item_id})
        state.last_operator = op_id

        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "shift_event",
            "end",
            "reported",
            {"handover_id": handover_ref},
            shift_end,
            "site",
        )
        self.shifts.append(
            {
                "shift_id": shift_id,
                "site_id": site_id,
                "machine_id": mid,
                "operator_id": op_id,
                "started_at": iso_utc(shift_start),
                "ended_at": iso_utc(shift_end),
                "local_shift_date": day.strftime("%Y-%m-%d"),
                "shift_code": shift_code,
                "data_origin": self.origin,
                "recorded_at": iso_utc(shift_start),
            }
        )

    # ------------------------------------------------------------------ task

    def _pick_task(self, mclass: str, op_id: str) -> tuple[str, str, float, str]:
        rng = self.rng
        if mclass == "haul_truck":
            tt = str(rng.choice(["haul_overburden", "haul_ore"], p=[0.65, 0.35]))
            return (
                tt,
                ("overburden" if tt == "haul_overburden" else "ore"),
                float(rng.integers(6, 24) * 90),
                "t",
            )
        if op_id == DEMO_RAVI:
            if not self.ravi_trenching_done:
                self.ravi_trenching_done = True
                tt = "trenching"
            else:
                tt = str(rng.choice(["truck_loading", "backfilling", "grading"]))
        else:
            tt = str(
                rng.choice(
                    ["trenching", "truck_loading", "backfilling", "grading", "pipe_lifting"],
                    p=[0.33, 0.33, 0.14, 0.12, 0.08],
                )
            )
        if tt == "trenching":
            mat = (
                "clay"
                if op_id == DEMO_RAVI
                else str(
                    rng.choice(
                        ["clay", "sand", "gravel", "topsoil", "rock"], p=[0.35, 0.18, 0.17, 0.12, 0.18]
                    )
                )
            )
            return tt, mat, float(rng.integers(15, 55)), "m"
        if tt in ("truck_loading", "backfilling"):
            return (
                tt,
                str(rng.choice(["clay", "sand", "gravel", "rock"], p=[0.40, 0.25, 0.20, 0.15])),
                float(rng.integers(30, 110)),
                "m3",
            )
        if tt == "grading":
            return (
                tt,
                str(rng.choice(["clay", "sand", "gravel", "topsoil"], p=[0.35, 0.25, 0.25, 0.15])),
                float(rng.integers(150, 600)),
                "m2",
            )
        return tt, "any", float(rng.integers(3, 10)), "lifts"

    def _build_task(self, m, profile, site, op, exp_months, dev_id, shift_id, day, week, seq, start_utc):
        rng = self.rng
        mid, mclass, site_id = m["machine_id"], m["machine_class"], site["site_id"]
        op_id = op["operator_id"]
        offset = timedelta(minutes=site["utc_offset_minutes"])
        tt, mat, qty, unit = self._pick_task(mclass, op_id)
        zone = str(rng.choice(TASK_ZONES.get((site_id, tt), [SITE_DEFAULT_ZONE[site_id]])))
        zone_name = next((z["name"] for z in self.gen.zones if z["zone_id"] == zone), zone)
        tt_cfg = next(t for t in profile["task_types"] if t["task_type"] == tt)
        baseline = compute_baseline_minutes(profile, tt, mat, qty, site.get("job_efficiency_override"))
        if baseline is None:
            raise ValueError(f"No baseline for {mid} {tt} {mat}")
        task_id = f"T-{day.strftime('%Y%m%d')}-{mid.replace('-', '')}-{seq}"

        planned_start = None if rng.random() < 0.10 else start_utc
        window_min = int(rng.choice([15, 0, 30], p=[0.80, 0.10, 0.10]))
        estimate_at = start_utc - timedelta(minutes=15)
        ref = planned_start or estimate_at
        cond = self.condition_at(site, ref)
        local_ref = ref + offset
        dark = is_dark(local_ref, site)
        if cond:
            weather = derive_weather(cond)
            visibility = visibility_band(cond.get("visibility_m"), dark)
            temp_band = temperature_band(cond.get("temp_c"))
        else:
            weather, visibility, temp_band = None, None, None
        tod = time_of_day(local_ref.hour)
        congestion = self.gen.day_congestion[(site_id, day.strftime("%Y-%m-%d"))]
        machine_age = max(0, day.year - int(m.get("year_of_manufacture", 2021)))
        planner = round(
            baseline
            * self.raw["planner"].get("scale", 0.92)
            * math.exp(float(rng.normal(0, self.raw["planner"].get("sigma", 0.08)))),
            1,
        )
        rule_prefix = f"profile={m['profile_id']}@{m.get('profile_version', 1)}"

        common = {
            "task_id": task_id,
            "assignment_revision": 1,
            "site_id": site_id,
            "zone_id": zone,
            "machine_id": mid,
            "operator_id": op_id,
            "shift_id": shift_id,
            "task_type": tt,
            "material": mat,
            "quantity": qty,
            "unit": unit,
            "location_text": zone_name,
            "priority": 1 if seq == 1 else 2,
            "completion_criterion": f"{tt.replace('_', ' ').capitalize()} {qty:g} {unit} at {zone_name}",
            "assignment_source": "dispatcher",
            "planned_date": day.strftime("%Y-%m-%d"),
            "sequence": seq,
            "planned_start_at": iso_utc(planned_start) if planned_start else None,
            "planned_start_window_min": window_min,
            "estimate_requested_at": iso_utc(estimate_at),
            "planner_minutes": planner,
            "profile_id": m["profile_id"],
            "profile_version": int(m.get("profile_version", 1)),
            "skill_level_at_start": op["skill_level"],
            "experience_months_at_start": exp_months,
            "machine_age_years_at_start": machine_age,
            "condition_id": cond["condition_id"] if cond else None,
            "weather_at_start": weather,
            "visibility_at_start": visibility,
            "temperature_band_at_start": temp_band,
            "time_of_day_at_start": tod,
            "site_congestion_at_start": congestion,
            "darkness_at_start": dark,
            "baseline_minutes": baseline,
            "data_origin": self.origin,
        }

        # Cancelled by the supervisor before starting (§7.4.2): no outcome, not training eligible
        if op_id != DEMO_RAVI and rng.random() < self.raw.get("task_events", {}).get("cancel_prob", 0.0):
            self.ledger_entry(
                dev_id,
                shift_id,
                mid,
                op_id,
                "task_event",
                "cancel",
                "reviewed",
                {
                    "task_id": task_id,
                    "assignment_revision": 1,
                    "reason_code": None,
                    "output_qty": None,
                    "actual_start": None,
                    "actual_end": None,
                    "active_min": None,
                    "waiting_min": None,
                    "break_min": None,
                    "paused_min": None,
                },
                start_utc,
                "site",
                rule="supervisor_reassignment@1",
            )
            self.tasks.append(
                {
                    **common,
                    "status": "CANCELLED",
                    "actual_start_at": None,
                    "actual_end_at": None,
                    "actual_active_min": None,
                    "actual_waiting_min": None,
                    "actual_break_min": None,
                    "actual_paused_min": None,
                    "actual_elapsed_min": None,
                    "output_qty": None,
                    "completion_quality": "not_applicable",
                    "training_eligible": False,
                    "training_exclusion_reason": "cancelled",
                    "split_temporal": "excluded",
                    "split_unseen_operator": "excluded",
                    "recorded_at": iso_utc(start_utc),
                }
            )
            return None

        # Forecast used for the estimate (logged once per machine and forecast hour)
        if cond and (mid, cond["condition_id"]) not in self.forecast_logged:
            self.forecast_logged.add((mid, cond["condition_id"]))
            issued = datetime.fromisoformat(cond["issued_at"])
            self.ledger_entry(
                dev_id,
                shift_id,
                mid,
                op_id,
                "observation",
                "condition_forecast",
                "observed",
                {
                    "site_id": site_id,
                    "valid_from": cond["valid_from"],
                    "valid_to": cond["valid_to"],
                    "weather": cond["weather"],
                    "visibility": cond["visibility"],
                    "visibility_m": cond["visibility_m"],
                    "temp_c": cond["temp_c"],
                    "heat_index_c": cond["heat_index_c"],
                    "wind_kmh": cond["wind_kmh"],
                    "precipitation_mm": cond["precipitation_mm"],
                    "issued_at": cond["issued_at"],
                    "source": "seed",
                },
                issued,
                "site",
                freshness_s=None,
            )

        # Active work minutes from the effect model (§8.22)
        effects = self.cfg.effects
        mult, _ = compute_task_effects(
            effects,
            skill_level=op["skill_level"],
            experience_months=exp_months,
            weather=weather or "clear",
            visibility=visibility or "good",
            temp_band=temp_band or "mild",
            time_of_day=tod,
            congestion=congestion,
            machine_age_years=machine_age,
            material=mat,
            is_wind_sensitive=bool(tt_cfg.get("wind_sensitive")),
            task_type=tt,
            operator_effect=self.gen.operator_effects[op_id],
            site_effect=self.gen.site_effects[site_id],
            noise=sample_task_noise(rng, baseline, effects.get("noise_variance", {})),
            effect_scale=self.scale,
        )
        work_min = (
            baseline
            * mult
            * math.exp(self.raw.get("calibration", {}).get("log_intercept_by_class", {}).get(mclass, 0.0))
        )

        # Interruptions: waits (reported / unexplained), pause, block
        interruptions = self._sample_interruptions(tt, mclass, op_id, congestion, weather)
        n = len(interruptions)
        chunk = work_min / (n + 1)
        t = start_utc
        intervals: list[Interval] = []
        timeline: list[tuple[datetime, datetime, dict[str, Any]]] = []
        for spec in interruptions:
            t += timedelta(minutes=chunk)
            end = t + timedelta(minutes=spec["minutes"])
            timeline.append((t, end, spec))
            t = end
        end_utc = t + timedelta(minutes=chunk)

        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "inference",
            "estimate",
            "inferred",
            {
                "task_id": task_id,
                "task_type": tt,
                "basis": "fallback",
                "baseline_min": baseline,
                "p10_min": round(baseline * 0.8, 1),
                "p50_min": round(baseline, 1),
                "p90_min": round(baseline * 1.35, 1),
                "expected_wait_min": float(tt_cfg.get("default_expected_wait_min", 5)),
                "factors": [],
                "artifact_id": "baseline-fallback@1",
                "personal_offset": None,
                "context": {
                    "weather": weather,
                    "visibility": visibility,
                    "temperature_band": temp_band,
                    "time_of_day": tod,
                    "site_congestion": congestion,
                    "darkness": dark,
                },
            },
            estimate_at,
            "site",
            rule=f"estimate@1;{rule_prefix}",
            confidence="medium",
        )
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "task_event",
            "start",
            "reported",
            self._task_payload(task_id),
            start_utc,
            "site",
        )

        waiting = brk = paused = unexplained_idle = 0.0
        for s, e, spec in timeline:
            minutes = (e - s).total_seconds() / 60.0
            if spec["type"] == "pause":
                paused += minutes
                intervals.append(Interval("pause", s, e))
                self.ledger_entry(
                    dev_id,
                    shift_id,
                    mid,
                    op_id,
                    "task_event",
                    "pause",
                    "reported",
                    self._task_payload(task_id),
                    s,
                    "site",
                )
                self.ledger_entry(
                    dev_id,
                    shift_id,
                    mid,
                    op_id,
                    "task_event",
                    "resume",
                    "reported",
                    self._task_payload(task_id),
                    e,
                    "site",
                )
            elif spec["type"] == "block":
                waiting += minutes
                intervals.append(Interval("block", s, e))
                self.ledger_entry(
                    dev_id,
                    shift_id,
                    mid,
                    op_id,
                    "task_event",
                    "block",
                    "reported",
                    {**self._task_payload(task_id), "reason_code": spec["reason"]},
                    s,
                    "site",
                )
                self.ledger_entry(
                    dev_id,
                    shift_id,
                    mid,
                    op_id,
                    "task_event",
                    "resume",
                    "reported",
                    self._task_payload(task_id),
                    e,
                    "site",
                )
            else:
                category = self._idle(dev_id, shift_id, m, op_id, site, task_id, zone, s, e, spec)
                intervals.append(Interval("idle", s, e, spec["idle_class"], category))
                if category == "break":
                    brk += minutes
                elif category in ("site_delay", "other"):
                    waiting += minutes
                else:
                    unexplained_idle += minutes  # unexplained idle stays active (§8.6.7)

        elapsed = (end_utc - start_utc).total_seconds() / 60.0
        active = round(elapsed - waiting - brk - paused, 1)
        waiting, brk, paused = round(waiting, 1), round(brk, 1), round(paused, 1)
        elapsed = round(active + waiting + brk + paused, 1)
        end_utc = start_utc + timedelta(minutes=elapsed)

        partial = rng.random() < 0.02
        output = round(qty * float(rng.uniform(0.3, 0.8)), 1) if partial else qty
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "task_event",
            "complete",
            "reported",
            {
                "task_id": task_id,
                "assignment_revision": 1,
                "reason_code": None,
                "output_qty": output,
                "actual_start": iso_utc(start_utc),
                "actual_end": iso_utc(end_utc),
                "active_min": active,
                "waiting_min": waiting,
                "break_min": brk,
                "paused_min": paused,
            },
            end_utc,
            "site",
        )

        eligible = not partial and active > 0
        if eligible:
            split_a = "train" if week <= 8 else ("calibration" if week <= 10 else "test")
            if op_id in self.held_out:
                split_b = "test"
            else:
                split_b = "train" if week <= 8 else ("calibration" if week <= 10 else "excluded")
        else:
            split_a = split_b = "excluded"
        self.tasks.append(
            {
                **common,
                "status": "COMPLETED",
                "actual_start_at": iso_utc(start_utc),
                "actual_end_at": iso_utc(end_utc),
                "actual_active_min": active,
                "actual_waiting_min": waiting,
                "actual_break_min": brk,
                "actual_paused_min": paused,
                "actual_elapsed_min": elapsed,
                "output_qty": output,
                "completion_quality": "partial" if partial else "confirmed",
                "training_eligible": eligible,
                "training_exclusion_reason": "partial_completion" if partial else None,
                "split_temporal": split_a,
                "split_unseen_operator": split_b,
                "recorded_at": iso_utc(end_utc),
            }
        )

        heavy_load = tt in ("truck_loading", "trenching") and mat in ("clay", "rock", "gravel")
        load_pct = float(rng.uniform(62, 82)) if heavy_load else float(rng.uniform(38, 58))
        self._summaries(
            dev_id, shift_id, m, op_id, site, task_id, start_utc, end_utc, intervals, load_pct, rule_prefix
        )
        self._alerts(
            dev_id,
            shift_id,
            m,
            op_id,
            op,
            site,
            task_id,
            zone,
            start_utc,
            end_utc,
            weather,
            dark,
            rule_prefix,
        )
        return (
            end_utc,
            heavy_load and load_pct >= self.raw.get("required_idle", {}).get("cooldown_load_pct", 60),
            zone,
        )

    @staticmethod
    def _task_payload(task_id: str) -> dict[str, Any]:
        return {
            "task_id": task_id,
            "assignment_revision": 1,
            "reason_code": None,
            "output_qty": None,
            "actual_start": None,
            "actual_end": None,
            "active_min": None,
            "waiting_min": None,
            "break_min": None,
            "paused_min": None,
        }

    def _sample_interruptions(self, tt, mclass, op_id, congestion, weather) -> list[dict[str, Any]]:
        rng = self.rng
        waits = self.raw["waits"]
        lam = waits["lambda_by_task_type"].get(tt, 0.5)
        lam *= waits.get("congestion_multiplier", {}).get(congestion, 1.0)
        if weather == "rain":
            lam *= waits.get("rain_multiplier", 1.0)
        n_waits = int(rng.poisson(lam))
        if op_id in self.gen.habitual_unexplained_ops and rng.random() < 0.4:
            n_waits += 1
        weights = waits["reason_weights"]["haul" if mclass == "haul_truck" else tt]
        reasons, probs = list(weights), np.array(list(weights.values()), dtype=float)
        probs = probs / probs.sum()
        out = []
        for _ in range(n_waits):
            minutes = float(
                np.clip(
                    rng.lognormal(
                        math.log(waits["duration_lognormal_median_min"]), waits["duration_lognormal_sigma"]
                    ),
                    2.0,
                    45.0,
                )
            )
            unexplained = rng.random() >= waits.get("reported_prob", 0.85) or (
                op_id in self.gen.habitual_unexplained_ops and rng.random() < 0.3
            )
            spec = {
                "type": "idle",
                "minutes": round(minutes, 1),
                "idle_class": "unexplained" if unexplained else "reported",
                "reason": None if unexplained else str(rng.choice(reasons, p=probs)),
            }
            out.append(spec)
        te = self.raw.get("task_events", {})
        if rng.random() < te.get("pause_prob", 0.0):
            lo, hi = te.get("pause_min", [3, 12])
            out.append({"type": "pause", "minutes": round(float(rng.uniform(lo, hi)), 1)})
        if rng.random() < te.get("block_prob", 0.0):
            lo, hi = te.get("block_min", [8, 30])
            out.append(
                {
                    "type": "block",
                    "minutes": round(float(rng.uniform(lo, hi)), 1),
                    "reason": str(
                        rng.choice(["access_blocked", "utility_mark", "waiting_instruction", "weather"])
                    ),
                }
            )
        rng.shuffle(out)
        return out

    # ------------------------------------------------------------------ idle

    def _idle(self, dev_id, shift_id, m, op_id, site, task_id, zone, s, e, spec) -> str | None:
        """A non-required idle inside a task. Returns the effective time category (None if unexplained)."""
        rng = self.rng
        mid = m["machine_id"]
        idle_id = self.uid(f"idle:{mid}")
        dur = round((e - s).total_seconds())
        prompted = s + timedelta(seconds=IDLE_THRESHOLD_S) if dur >= IDLE_THRESHOLD_S else None
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "idle_event",
            "started",
            "observed",
            {
                "idle_event_id": idle_id,
                "candidate_started_at": iso_utc(s),
                "task_id": task_id,
                "zone_id": zone,
            },
            s,
            "site",
        )
        reason = spec.get("reason")
        report_entry = None
        reason_at = None
        category = None
        corrected = None
        if reason:
            # Answered at the prompt (or given early for short waits)
            reason_at = (
                prompted + timedelta(seconds=int(rng.integers(5, 40)))
                if prompted
                else s + timedelta(seconds=int(min(dur - 5, max(20, dur // 2))))
            )
            report_entry = self.ledger_entry(
                dev_id,
                shift_id,
                mid,
                op_id,
                "report",
                "idle_reason",
                "reported",
                {
                    "idle_event_id": idle_id,
                    "reason_code": reason,
                    "free_text": None,
                    "via": str(rng.choice(["button", "voice"])),
                },
                reason_at,
                "site",
            )
            # Explain-once corrections: a site delay later corrected to another site delay (§8.9 demo story)
            if reason in SITE_DELAY_REASONS and rng.random() < self.raw["waits"].get("correction_prob", 0.0):
                options = [
                    r for r in sorted(SITE_DELAY_REASONS) if r != reason and r in self._machine_reasons(m)
                ]
                corrected = str(rng.choice(options)) if options else None
        effective = corrected or reason
        if effective:
            category = (
                "site_delay"
                if effective in SITE_DELAY_REASONS
                else ("break" if effective == "break" else "other")
            )

        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "idle_event",
            "ended",
            "observed",
            {"idle_event_id": idle_id, "ended_at": iso_utc(e), "duration_s": dur, "required_s": 0},
            e,
            "site",
        )
        idle_class = "reported" if reason else "unexplained"
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "inference",
            "idle_classification",
            "inferred",
            {
                "idle_event_id": idle_id,
                "idle_class": idle_class,
                "required_s": 0,
                "non_required_s": dur,
                "category": category,
            },
            e,
            "site",
            rule=f"idle@1;profile={m['profile_id']}@{m.get('profile_version', 1)}",
            confidence="high",
        )

        finding = None
        if reason in SITE_DELAY_REASONS:
            finding = self._site_delay_finding(
                dev_id, shift_id, m, op_id, site, idle_id, zone, reason, dur, e, report_entry["entry_id"]
            )
        if corrected and report_entry is not None:
            fix_at = e + timedelta(minutes=float(rng.uniform(2, 40)))
            self.ledger_entry(
                dev_id,
                shift_id,
                mid,
                op_id,
                "correction",
                "idle_reason",
                "reported",
                {
                    "target_kind": "report",
                    "target_subtype": "idle_reason",
                    "replacement": {
                        "idle_event_id": idle_id,
                        "reason_code": corrected,
                        "free_text": None,
                        "via": "voice",
                    },
                },
                fix_at,
                "site",
                supersedes=report_entry["entry_id"],
                original_text=f"actually, {corrected.replace('_', ' ')}",
            )
            if finding is not None:
                replacement = dict(
                    finding["payload"], reason_code=corrected, possible_explanations=[corrected]
                )
                self.ledger_entry(
                    dev_id,
                    shift_id,
                    mid,
                    op_id,
                    "correction",
                    "finding",
                    "inferred",
                    {"target_kind": "inference", "target_subtype": "finding", "replacement": replacement},
                    fix_at + timedelta(seconds=1),
                    "site",
                    supersedes=finding["entry_id"],
                    rule="findings@1",
                )

        self.idles.append(
            {
                "idle_event_id": idle_id,
                "site_id": site["site_id"],
                "machine_id": mid,
                "operator_id": op_id,
                "shift_id": shift_id,
                "task_id": task_id,
                "zone_id": zone,
                "started_at": iso_utc(s),
                "ended_at": iso_utc(e),
                "recorded_at": iso_utc(e),
                "duration_s": dur,
                "required_s": 0,
                "non_required_s": dur,
                "required_basis": "none",
                "idle_class": idle_class,
                "reason_code": effective,
                "reason_entry_id": report_entry["entry_id"] if report_entry else None,
                "reason_recorded_at": iso_utc(reason_at) if reason_at else None,
                "category": category,
                "prompted_at": iso_utc(prompted) if prompted else None,
                "prompt_answered_at": iso_utc(reason_at)
                if (prompted and reason_at and reason_at >= prompted)
                else None,
                "sensor_coverage_pct": 100.0,
                "evidence_status": "reported" if reason else "unresolved",
                "data_origin": self.origin,
            }
        )
        return category

    def _machine_reasons(self, m: dict[str, Any]) -> list[str]:
        return self.gen.profiles[m["profile_id"]]["idle"]["reasons"]

    def _site_delay_finding(
        self, dev_id, shift_id, m, op_id, site, idle_id, zone, reason, dur, at, report_id
    ):
        local_date = (at + timedelta(minutes=site["utc_offset_minutes"])).strftime("%Y-%m-%d")
        payload = {
            "finding_id": self.uid("finding"),
            "subject_id": idle_id,
            "pattern_code": "idle_reported_wait",
            "owner": "site",
            "evidence_status": "reported",
            "reason_key": "finding.idle_reported_wait",
            "observed": {"text_key": "finding.observed.idle_wait", "params": {"minutes": round(dur / 60, 1)}},
            "possible_explanations": [reason],
            "related_entry_ids": [report_id],
            "machine_id": m["machine_id"],
            "site_id": site["site_id"],
            "zone_id": zone,
            "reason_code": reason,
            "minutes": round(dur / 60, 1),
            "local_date": local_date,
            "rule_version": "findings@1",
        }
        return self.ledger_entry(
            dev_id,
            shift_id,
            m["machine_id"],
            op_id,
            "inference",
            "finding",
            "inferred",
            payload,
            at + timedelta(seconds=2),
            "site",
            rule="findings@1",
            confidence="high",
        )

    def _required_idle(self, dev_id, shift_id, m, op_id, site, task_id, zone, s, dur, basis):
        """Warm-up / cool-down idle (§8.7): required, never prompted, no reason, no follow-up."""
        mid = m["machine_id"]
        idle_id = self.uid(f"idle-req:{mid}")
        e = s + timedelta(seconds=dur)
        required = min(dur, int(self.raw["required_idle"].get(f"{basis}_s", 300)))
        non_required = dur - required
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "idle_event",
            "started",
            "observed",
            {
                "idle_event_id": idle_id,
                "candidate_started_at": iso_utc(s),
                "task_id": task_id,
                "zone_id": zone,
            },
            s,
            "site",
        )
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "idle_event",
            "ended",
            "observed",
            {"idle_event_id": idle_id, "ended_at": iso_utc(e), "duration_s": dur, "required_s": required},
            e,
            "site",
        )
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "inference",
            "idle_classification",
            "inferred",
            {
                "idle_event_id": idle_id,
                "idle_class": "required",
                "required_s": required,
                "non_required_s": non_required,
                "category": None,
            },
            e,
            "site",
            rule=f"idle@1;profile={m['profile_id']}@{m.get('profile_version', 1)}",
            confidence="high",
        )
        self.idles.append(
            {
                "idle_event_id": idle_id,
                "site_id": site["site_id"],
                "machine_id": mid,
                "operator_id": op_id,
                "shift_id": shift_id,
                "task_id": task_id,
                "zone_id": zone,
                "started_at": iso_utc(s),
                "ended_at": iso_utc(e),
                "recorded_at": iso_utc(e),
                "duration_s": dur,
                "required_s": required,
                "non_required_s": non_required,
                "required_basis": basis,
                "idle_class": "required",
                "reason_code": None,
                "reason_entry_id": None,
                "reason_recorded_at": None,
                "category": None,
                "prompted_at": None,
                "prompt_answered_at": None,
                "sensor_coverage_pct": 100.0,
                "evidence_status": "corroborated",
                "data_origin": self.origin,
            }
        )

    # ------------------------------------------------------------------ summaries

    def _summaries(
        self, dev_id, shift_id, m, op_id, site, task_id, start, end, intervals, load_pct, rule_prefix
    ):
        rng = self.rng
        mid, mclass = m["machine_id"], m["machine_class"]
        sensors = self.raw.get("sensors", {})
        cursor = start
        while cursor < end:
            w_end = min(end, cursor + timedelta(minutes=5))
            win = int((w_end - cursor).total_seconds())
            if win < 60:
                break
            idle_s = secured_s = 0
            for iv in intervals:
                ov = (min(w_end, iv.end) - max(cursor, iv.start)).total_seconds()
                if ov > 0:
                    if iv.kind == "idle":
                        idle_s += int(ov)
                    else:
                        secured_s += int(ov)
            idle_s = min(idle_s, win)
            secured_s = min(secured_s, win - idle_s)
            ready_s = idle_s
            moving = win - idle_s - secured_s
            travelling = int(moving * 0.45) if mclass == "haul_truck" else 0
            working = moving - travelling

            missing: list[str] = []
            missing_s = 0
            unknown = 0
            if rng.random() < sensors.get("dropout_prob", 0.0):
                missing = [str(rng.choice(sensors.get("dropout_signals", ["fuel_used_l"])))]
                lo, hi = sensors.get("dropout_seconds", [10, 120])
                missing_s = int(min(win - 1, rng.integers(lo, hi + 1)))
                if missing[0] in ("ground_speed_kmh", "load_factor_pct"):
                    unknown = min(missing_s, working)
                    working -= unknown
            idle_total = idle_s + secured_s
            burn_lph = (16.0 if mclass == "excavator" else 55.0) * (load_pct / 65.0)
            fuel = round(
                (working + travelling) / 3600 * burn_lph
                + idle_total / 3600 * (3.5 if mclass == "excavator" else 12.0),
                3,
            )
            if mclass == "excavator":
                cycles = round(working / 3600 * 150 * rng.uniform(0.85, 1.1))
                max_speed = round(float(rng.uniform(0.5, 3.5)), 1)
            else:
                cycles = int(rng.random() < win / 720)
                max_speed = round(float(rng.uniform(18.0, 34.0)), 1)
            payload = {
                "window_start": epoch_ms(cursor),
                "window_end": epoch_ms(w_end),
                "engine_on_s": win,
                "secured_s": secured_s,
                "ready_s": ready_s,
                "working_s": working,
                "travelling_s": travelling,
                "unknown_s": unknown,
                "idle_s": idle_total,
                "fuel_used_l": None if "fuel_used_l" in missing else fuel,
                "load_cycles": cycles,
                "max_speed_kmh": None if "ground_speed_kmh" in missing else max_speed,
                "avg_load_factor_pct": None
                if "load_factor_pct" in missing
                else round(load_pct + float(rng.normal(0, 4)), 1),
                "belt_unfastened_moving_s": None if "seatbelt_fastened" in missing else 0,
                "samples": win - missing_s,
                "missing_samples": missing_s,
                "missing_signal_names": missing,
            }
            entry = self.ledger_entry(
                dev_id,
                shift_id,
                mid,
                op_id,
                "observation",
                "signal_summary_5m",
                "observed",
                payload,
                w_end,
                "site",
                freshness_s=0.0,
            )
            self.summaries.append(
                {
                    "summary_id": entry["entry_id"],
                    "site_id": site["site_id"],
                    "machine_id": mid,
                    "shift_id": shift_id,
                    "task_id": task_id,
                    "window_start": iso_utc(cursor),
                    "window_end": iso_utc(w_end),
                    "recorded_at": iso_utc(w_end),
                    **{
                        k: payload[k]
                        for k in (
                            "engine_on_s",
                            "secured_s",
                            "ready_s",
                            "working_s",
                            "travelling_s",
                            "unknown_s",
                            "idle_s",
                            "fuel_used_l",
                            "load_cycles",
                            "max_speed_kmh",
                            "avg_load_factor_pct",
                            "belt_unfastened_moving_s",
                            "samples",
                            "missing_samples",
                        )
                    },
                    "missing_signal_names": json.dumps(missing),
                    "profile_id": m["profile_id"],
                    "profile_version": int(m.get("profile_version", 1)),
                    "data_origin": self.origin,
                }
            )
            cursor = w_end

    # ------------------------------------------------------------------ alerts & incidents

    def _alert_rows(
        self,
        dev_id,
        shift_id,
        m,
        op_id,
        site,
        task_id,
        zone,
        alert: dict[str, Any],
        transitions: list[tuple[str, datetime, str | None]],
        rule: str,
    ) -> None:
        for transition, at, clear_reason in transitions:
            source = "reported" if transition == "acknowledged" else "observed"
            payload = {
                "alert_id": alert["alert_id"],
                "alert_type": alert["alert_type"],
                "level": alert["level"],
                "group_key": alert["group_key"],
                "zone_id": zone,
                "object_id": alert.get("object_id"),
                "object_type": alert.get("object_type"),
                "place": alert.get("place"),
                "distance_m": alert.get("distance_m"),
                "ttc_s": alert.get("ttc_s"),
                "multiplier": alert.get("multiplier"),
                "occurrences": 1,
                "clear_reason": clear_reason if transition == "cleared" else None,
                "safe_exit": alert.get("safe_exit"),
            }
            entry = self.ledger_entry(
                dev_id,
                shift_id,
                m["machine_id"],
                op_id,
                "alert",
                transition,
                source,
                payload,
                at,
                "site",
                rule=rule,
            )
            self.alerts.append(
                {
                    "alert_event_id": entry["entry_id"],
                    "alert_id": alert["alert_id"],
                    "site_id": site["site_id"],
                    "machine_id": m["machine_id"],
                    "shift_id": shift_id,
                    "task_id": task_id,
                    "zone_id": zone,
                    "transition": transition,
                    "alert_type": alert["alert_type"],
                    "level": alert["level"],
                    "group_key": alert["group_key"],
                    "occurrences": 1,
                    "object_id": alert.get("object_id"),
                    "object_type": alert.get("object_type"),
                    "place": alert.get("place"),
                    "distance_m": alert.get("distance_m"),
                    "ttc_s": alert.get("ttc_s"),
                    "multiplier": alert.get("multiplier"),
                    "clear_reason": payload["clear_reason"],
                    "exit_cue": (alert.get("safe_exit") or {}).get("exit_cue"),
                    "safe_exit_json": json.dumps(alert["safe_exit"], sort_keys=True)
                    if alert.get("safe_exit")
                    else None,
                    "observed_at": iso_utc(at),
                    "recorded_at": iso_utc(at),
                    "source": source,
                    "rule_or_model_version": rule,
                    "profile_id": m["profile_id"],
                    "profile_version": int(m.get("profile_version", 1)),
                    "data_origin": self.origin,
                }
            )

    def _alerts(
        self, dev_id, shift_id, m, op_id, op, site, task_id, zone, start, end, weather, dark, rule_prefix
    ):
        rng = self.rng
        span_min = max(1.0, (end - start).total_seconds() / 60 - 2)
        mclass = m["machine_class"]

        def at(frac_lo=0.05, frac_hi=0.95) -> datetime:
            return start + timedelta(minutes=float(rng.uniform(frac_lo, frac_hi)) * span_min)

        # Seatbelt while operating — A-BELT-OPER WARNING (beginners ~4x more often)
        if rng.random() < (0.08 if op["skill_level"] == "beginner" else 0.02):
            t0 = at()
            alert = {
                "alert_id": self.uid("alert"),
                "alert_type": "A-BELT-OPER",
                "level": "WARNING",
                "group_key": "belt",
            }
            tr = [("raised", t0, None)]
            if rng.random() < 0.6:
                tr.append(("acknowledged", t0 + timedelta(seconds=float(rng.uniform(3, 12))), None))
            tr.append(("cleared", tr[-1][1] + timedelta(seconds=float(rng.uniform(4, 20))), "belt_fastened"))
            self._alert_rows(
                dev_id, shift_id, m, op_id, site, task_id, zone, alert, tr, f"seatbelt@1;{rule_prefix}"
            )

        # Overspeed on haul roads — A-SPEED WARNING (3 habitual operators)
        if mclass == "haul_truck" and rng.random() < (
            0.12 if op_id in self.gen.habitual_overspeed_ops else 0.02
        ):
            t0 = at()
            alert = {
                "alert_id": self.uid("alert"),
                "alert_type": "A-SPEED",
                "level": "WARNING",
                "group_key": "speed",
            }
            self._alert_rows(
                dev_id,
                shift_id,
                m,
                op_id,
                site,
                task_id,
                zone,
                alert,
                [
                    ("raised", t0, None),
                    ("cleared", t0 + timedelta(seconds=float(rng.uniform(8, 25))), "below_limit"),
                ],
                f"overspeed@1;{rule_prefix}",
            )

        # Proximity — CAUTION, sometimes WARNING (which auto-creates an incident, F7-R4)
        if rng.random() < 0.06:
            t0 = at()
            obj_type = str(rng.choice(["person", "light_vehicle", "heavy_vehicle"], p=[0.5, 0.3, 0.2]))
            obj_id = (
                f"P{int(rng.integers(1, 99))}" if obj_type == "person" else f"V{int(rng.integers(1, 99))}"
            )
            mult = 1.0
            if weather == "rain":
                mult *= 1.25
            if weather == "dusty":
                mult *= 1.3
            if dark:
                mult *= 1.3
            mult = round(min(1.6, mult), 3)
            warning = rng.random() < 0.3
            place = str(rng.choice(PLACES))
            alert = {
                "alert_id": self.uid("alert"),
                "alert_type": "A-PROX-WARN" if warning else "A-PROX-CAUT",
                "level": "WARNING" if warning else "CAUTION",
                "group_key": f"prox:{obj_id}",
                "object_id": obj_id,
                "object_type": obj_type,
                "place": place,
                "distance_m": round(
                    float(rng.uniform(3.0, 4.4) if warning else rng.uniform(5.0, 9.0)) * mult, 1
                ),
                "ttc_s": round(float(rng.uniform(1.5, 2.9) if warning else rng.uniform(3.2, 5.8)), 1),
                "multiplier": mult,
            }
            t_clear = t0 + timedelta(seconds=float(rng.uniform(6, 30)))
            self._alert_rows(
                dev_id,
                shift_id,
                m,
                op_id,
                site,
                task_id,
                zone,
                alert,
                [("raised", t0, None), ("cleared", t_clear, "object_clear")],
                f"proximity@1;{rule_prefix}",
            )
            if warning:
                self._incident(dev_id, shift_id, m, op_id, site, zone, task_id, alert, t0, end, weather, dark)

        # Safe Exit Guard — rare A-EXIT-UNSEC advisory during an unsecured stop
        if rng.random() < 0.004:
            t0 = at()
            cue = str(rng.choice(["door_open", "seat_vacant", "both"]))
            safe_exit = {
                "belt_transition_at": iso_utc(t0 - timedelta(seconds=float(rng.uniform(1, 9)))),
                "exit_cue": cue,
                "inputs": {
                    "seatbelt_fastened": {"value": False, "fresh": True},
                    "seat_occupied": {"value": cue == "door_open", "fresh": True},
                    "cab_door_open": {"value": cue != "seat_vacant", "fresh": True},
                    "implement_neutral": {"value": False, "fresh": True},
                    "ground_speed_kmh": {"value": 0.0, "fresh": True},
                    self.gen.profiles[m["profile_id"]]["secure_signal"]: {"value": False, "fresh": True},
                },
                "unavailable_signals": [],
            }
            alert = {
                "alert_id": self.uid("alert"),
                "alert_type": "A-EXIT-UNSEC",
                "level": "ADVISORY",
                "group_key": "safe_exit",
                "safe_exit": safe_exit,
            }
            self._alert_rows(
                dev_id,
                shift_id,
                m,
                op_id,
                site,
                task_id,
                zone,
                alert,
                [
                    ("raised", t0, None),
                    ("cleared", t0 + timedelta(seconds=float(rng.uniform(8, 40))), "secured"),
                ],
                f"safe_exit@1;{rule_prefix}",
            )

    def _incident(self, dev_id, shift_id, m, op_id, site, zone, task_id, alert, t0, task_end, weather, dark):
        """Auto incident for a proximity WARNING (§7.4.5, §8.11) with the full hash-chained family."""
        rng = self.rng
        mid = m["machine_id"]
        incident_id = self.uid("incident")
        zone_row = next((z for z in self.gen.zones if z["zone_id"] == zone), None)
        lat = zone_row["center_lat"] if zone_row else site["lat"]
        lon = zone_row["center_lon"] if zone_row else site["lon"]
        pre = [
            {
                "ts": epoch_ms(t0 - timedelta(seconds=60 - i * 6)),
                "state": "WORKING",
                "speed_kmh": 2.0,
                "belt": True,
                "secure": False,
                "lat": lat,
                "lon": lon,
                "heading_deg": 90,
                "load_factor_pct": 55,
            }
            for i in range(10)
        ]
        snapshot = {
            "pre_s": 60,
            "post_s": 30,
            "samples": pre,
            "proximity": [
                {
                    "ts": epoch_ms(t0),
                    "object_id": alert["object_id"],
                    "type": alert["object_type"],
                    "bearing_deg": PLACES.index(alert["place"]) * 45,
                    "distance_m": alert["distance_m"],
                    "closing_mps": 1.1,
                }
            ],
            "alerts": [{"ts": epoch_ms(t0), "alert_type": alert["alert_type"], "level": alert["level"]}],
        }
        created = {
            "incident_id": incident_id,
            "origin": "auto",
            "trigger_alert_id": alert["alert_id"],
            "occurred_at": iso_utc(t0),
            "zone_id": zone,
            "observed": {
                "machine_state": "WORKING",
                "speed_kmh": 2.0,
                "belt_fastened": True,
                "secure_engaged": False,
                "lat": lat,
                "lon": lon,
                "detected": [
                    {
                        "object_id": alert["object_id"],
                        "type": alert["object_type"],
                        "place": alert["place"],
                        "min_distance_m": alert["distance_m"],
                    }
                ],
                "conditions": {"rain": weather == "rain", "dust": weather == "dusty", "darkness": dark},
                "active_task_id": task_id,
            },
            "snapshot": snapshot,
            "snapshot_complete": False,
            "severity_default": "high" if alert["object_type"] == "person" else "medium",
        }
        self.ledger_entry(
            dev_id, shift_id, mid, op_id, "incident", "created", "observed", created, t0, "safety"
        )
        post = [
            {
                "ts": epoch_ms(t0 + timedelta(seconds=i * 6)),
                "state": "WORKING",
                "speed_kmh": 1.0,
                "belt": True,
                "secure": False,
                "lat": lat,
                "lon": lon,
                "heading_deg": 90,
                "load_factor_pct": 50,
            }
            for i in range(1, 6)
        ]
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "incident",
            "snapshot_completed",
            "observed",
            {"incident_id": incident_id, "post_samples": post, "truncated": False},
            t0 + timedelta(seconds=30),
            "safety",
        )
        if rng.random() < 0.7:
            at = task_end + timedelta(minutes=float(rng.uniform(1, 6)))
            fields = {
                "type": "near_miss",
                "object": alert["object_type"],
                "place": alert["place"],
                "contact": "no",
            }
            self.ledger_entry(
                dev_id,
                shift_id,
                mid,
                op_id,
                "report",
                "incident_report",
                "reported",
                {
                    "incident_id": incident_id,
                    **fields,
                    "severity": created["severity_default"],
                    "via": "voice",
                },
                at,
                "safety",
                original_text=f"near miss, {alert['object_type'].replace('_', ' ')} {alert['place'].replace('_', ' ')}, no contact",
            )
            self.ledger_entry(
                dev_id,
                shift_id,
                mid,
                op_id,
                "inference",
                "incident_extraction",
                "inferred",
                {"incident_id": incident_id, "method": "rules", "fields": fields, "no_incident": False},
                at + timedelta(seconds=1),
                "safety",
                rule="incident_rules@1",
                confidence="high",
            )
            self.ledger_entry(
                dev_id,
                shift_id,
                mid,
                op_id,
                "incident",
                "status_changed",
                "reported",
                {"incident_id": incident_id, "status": "reported"},
                at + timedelta(seconds=2),
                "safety",
            )

    # ------------------------------------------------------------------ learning

    def _learning(self, dev_id, shift_id, mid, op_id, mclass, at):
        rng = self.rng
        content = str(rng.choice(LESSONS.get(mclass, LESSONS["excavator"])))
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "inference",
            "recommendation",
            "inferred",
            {
                "rec_id": self.uid("rec"),
                "content_id": content,
                "source": "task_prep",
                "pattern_code": None,
                "condition": None,
                "reason_key": "rec.reason.task_prep",
                "reason_params": {},
            },
            at,
            "operator_only",
            rule="recommender@1",
            confidence="medium",
        )
        base = {
            "content_id": content,
            "mode": "full",
            "question_index": None,
            "choice_index": None,
            "correct": None,
            "refresher_opt_in": None,
            "review_step": None,
        }
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "learning_event",
            "started",
            "reported",
            base,
            at + timedelta(minutes=1),
            "operator_only",
        )
        correct = bool(rng.random() < 0.75)
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "learning_event",
            "answered",
            "reported",
            {**base, "question_index": 0, "choice_index": 0 if correct else 1, "correct": correct},
            at + timedelta(minutes=2),
            "operator_only",
        )
        self.ledger_entry(
            dev_id,
            shift_id,
            mid,
            op_id,
            "learning_event",
            "completed",
            "reported",
            {**base, "refresher_opt_in": bool(rng.random() < 0.6)},
            at + timedelta(minutes=3),
            "operator_only",
        )
