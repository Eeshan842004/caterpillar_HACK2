import argparse
import csv
import hashlib
import json
import math
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from shiftmate_ml.datagen.config import GenConfig, load_config
from shiftmate_ml.datagen.history_export import export_demo_history
from shiftmate_ml.paths import (
    ASSUMPTIONS_PATH,
    CONFIG_PATH,
    GENERATED_DIR,
    PROFILES_DIR,
    SEED_PATH,
)


def iso_utc(dt: datetime) -> str:
    """Format datetime as ISO 8601 UTC with millisecond precision."""
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def deterministic_uuid(rng: np.random.Generator, tag: str) -> str:
    """Generate a deterministic UUID v4 string from seeded generator."""
    # Use 128 random bits from the generator
    high = int(rng.integers(0, 2**64, dtype=np.uint64))
    low = int(rng.integers(0, 2**64, dtype=np.uint64))
    val = (high << 64) | low
    # Set UUID v4 variant and version bits
    val &= ~(0xF000 << 64)
    val |= (0x4000 << 64)  # Version 4
    val &= ~(0xC000 << 48)
    val |= (0x8000 << 48)  # RFC 4122 variant
    return str(uuid.UUID(int=val))


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def generate_assumptions_doc(config: GenConfig, output_path: Path = ASSUMPTIONS_PATH) -> str:
    """Generates docs/GENERATOR_ASSUMPTIONS.md documenting all generator effects and parameters."""
    cfg = config.raw
    effects = cfg.get("effects", {})
    waits = cfg.get("waits", {})
    planner = cfg.get("planner", {})

    lines = [
        "# Throughline Synthetic Dataset Generator Assumptions",
        "",
        f"**Generator Version:** `{config.generator_version}`  ",
        f"**Schema Version:** `{config.schema_version}`  ",
        f"**Random Seed:** `{config.seed}`  ",
        f"**Anchor Date:** `{config.anchor_date}`  ",
        f"**Data Origin:** `{config.data_origin}`  ",
        "",
        "> [!IMPORTANT]",
        "> These parameters and multipliers are starting assumptions for synthetic prototype evaluation.",
        "> They do **not** represent measured physical Caterpillar telemetry or certified machine operational rates.",
        "",
        "## 1. Task Duration Model & Effects",
        "",
        "The actual active duration of a task is modeled as:",
        "```",
        "actual_active_min = baseline_min * exp(sum(effects) + operator_effect + site_effect + noise)",
        "```",
        "where baseline minutes are strictly derived from profile rate constants and site job efficiency (technical spec §8.6.1).",
        "",
        "### Effect Magnitudes and Rationales",
        "",
        "| Effect Domain | Key / Level | Value (log scale) | Rationale |",
        "|---|---|---|---|",
    ]

    # Skill
    skill_cfg = effects.get("skill", {})
    rat = skill_cfg.get("rationale", "")
    for k in ["beginner", "intermediate", "expert"]:
        v = skill_cfg.get(k, 0.0)
        lines.append(f"| Skill Level | `{k}` | `{v:+.2f}` | {rat} |")

    # Experience
    exp_cfg = effects.get("experience", {})
    lines.append(
        f"| Experience | `coef*(log1p(min(m, {exp_cfg.get('plateau_months')}))-{exp_cfg.get('anchor_log_months', 3.0)})` "
        f"| `coef={exp_cfg.get('coef', -0.06)}` | {exp_cfg.get('rationale', '')} |"
    )

    # Weather
    wx_cfg = effects.get("weather", {})
    rat = wx_cfg.get("rationale", "")
    for k in ["clear", "rain", "windy", "windy_sensitive_extra", "dusty", "foggy"]:
        v = wx_cfg.get(k, 0.0)
        lines.append(f"| Weather | `{k}` | `{v:+.2f}` | {rat} |")

    # Visibility
    vis_cfg = effects.get("visibility", {})
    rat = vis_cfg.get("rationale", "")
    for k in ["good", "moderate", "poor"]:
        v = vis_cfg.get(k, 0.0)
        lines.append(f"| Visibility | `{k}` | `{v:+.2f}` | {rat} |")

    # Temperature band
    temp_cfg = effects.get("temperature_band", {})
    rat = temp_cfg.get("rationale", "")
    for k in ["cool", "mild", "hot", "extreme"]:
        v = temp_cfg.get(k, 0.0)
        lines.append(f"| Temperature | `{k}` | `{v:+.2f}` | {rat} |")

    # Time of day
    tod_cfg = effects.get("time_of_day", {})
    rat = tod_cfg.get("rationale", "")
    for k in ["morning", "afternoon", "evening", "night"]:
        v = tod_cfg.get(k, 0.0)
        lines.append(f"| Time of Day | `{k}` | `{v:+.2f}` | {rat} |")

    # Congestion
    cong_cfg = effects.get("congestion", {})
    rat = cong_cfg.get("rationale", "")
    for k in ["low", "medium", "high"]:
        v = cong_cfg.get(k, 0.0)
        lines.append(f"| Site Congestion | `{k}` | `{v:+.2f}` | {rat} |")

    # Machine age
    age_cfg = effects.get("machine_age", {})
    lines.append(
        f"| Machine Age | per year | `+{age_cfg.get('coef_per_year', 0.012):.3f}` | {age_cfg.get('rationale', '')} |"
    )

    # Material
    mat_cfg = effects.get("material", {})
    rat = mat_cfg.get("rationale", "")
    for k in ["clay", "sand", "gravel", "topsoil", "rock", "overburden", "ore"]:
        v = mat_cfg.get(k, 0.0)
        lines.append(f"| Material | `{k}` | `{v:+.2f}` | {rat} |")

    # Interactions
    ix_cfg = effects.get("interactions", {})
    for k in ["rain_clay_trenching", "beginner_night", "beginner_rain", "high_congestion_haul"]:
        lines.append(f"| Interaction | `{k}` | `{ix_cfg.get(k, 0.0):+.2f}` | {ix_cfg.get('rationale', '')} |")

    noise = effects.get("noise_variance", {})
    calib = cfg.get("calibration", {})
    req = cfg.get("required_idle", {})
    te = cfg.get("task_events", {})
    sensors = cfg.get("sensors", {})

    # Random Variances
    lines.extend([
        f"| Operator Variance | Gaussian sigma | `N(0, {effects.get('operator_variance', {}).get('sigma', 0.06)})` | {effects.get('operator_variance', {}).get('rationale', '')} |",
        f"| Site Variance | Gaussian sigma | `N(0, {effects.get('site_variance', {}).get('sigma', 0.04)})` | {effects.get('site_variance', {}).get('rationale', '')} |",
        f"| Residual Noise | heteroscedastic, heavy-tailed | `sigma = {noise.get('sigma')} + {noise.get('small_task_extra_sigma')}*exp(-baseline/{noise.get('small_task_scale_min')})`; "
        f"disruption p={noise.get('disruption_prob')} adds U({noise.get('disruption_min')}, {noise.get('disruption_max')}) | {noise.get('rationale', '')} |",
        "",
        "### Calibration",
        "",
        f"Per-class log offset: `{calib.get('log_intercept_by_class', {})}`. {calib.get('rationale', '')}",
        "",
        "Resulting check (seed run): mean actual/baseline ≈ 1.08 for both classes; excavator planner bias ≈ +10 min on a "
        "43-minute median task (organiser: +6 min). Planner MAPE is ≈ 21–24%, higher than the organiser's 13.2%, because "
        "the synthetic set spans far more conditions than the organiser's five task rows; the spread is kept so the "
        "estimator has condition effects to learn. Re-tune once the full organiser data (E-01) is available.",
        "",
        "## 2. Dispatch Planner & Waiting Delays",
        "",
        f"- **Planner Estimate:** `baseline_min * {planner.get('scale', 0.92)} * exp(N(0, {planner.get('sigma', 0.08)}))`. {planner.get('rationale', '')}",
        f"- **Wait Arrivals:** Poisson process with rate lambda per task type. {waits.get('rationale', '')}",
        f"- **Wait Durations:** Lognormal distribution (median {waits.get('duration_lognormal_median_min', 9.0)} min, sigma {waits.get('duration_lognormal_sigma', 0.5)}).",
        f"- **Reporting Ratio:** {int(waits.get('reported_prob', 0.85)*100)}% reported by operator, {int(waits.get('unexplained_prob', 0.15)*100)}% unexplained.",
        f"- **Wait rate modifiers:** congestion `{waits.get('congestion_multiplier')}`, rain x{waits.get('rain_multiplier')}.",
        f"- **Reason mix by task type:** `{waits.get('reason_weights')}`.",
        f"- **Corrections:** {int(waits.get('correction_prob', 0) * 100)}% of reported site delays are later corrected to another site delay (explain-once history).",
        "",
        "## 3. Required idle, task events and sensors",
        "",
        f"- **Required idle:** cool-down after heavy loading (p={req.get('cooldown_prob')}, {req.get('cooldown_s')} s) and "
        f"cold-start warm-up (p={req.get('warmup_prob')}, {req.get('warmup_s')} s). {req.get('rationale', '')}",
        f"- **Task events:** pause p={te.get('pause_prob')}, block p={te.get('block_prob')}, cancel p={te.get('cancel_prob')}. {te.get('rationale', '')}",
        f"- **Sensor dropouts:** p={sensors.get('dropout_prob')} per 5-min window over `{sensors.get('dropout_signals')}`. {sensors.get('rationale', '')}",
        "- **Roster:** every machine class has beginners, intermediates and experts with overlapping experience; new hires "
        "only work after their hire date; experience is computed per task date.",
        "",
        "## 4. Sensitivity Runs",
        "",
        "Sensitivity benchmarks test model stability under scaled operational frictions:",
        "- `sens_0.5`: All environmental and operator effect terms scaled to 50%.",
        "- `sens_1.5`: All environmental and operator effect terms amplified to 150%.",
        "",
    ])

    doc_text = "\n".join(lines) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(doc_text)

    return hashlib.sha256(doc_text.encode("utf-8")).hexdigest()


class SyntheticGenerator:
    def __init__(self, config: GenConfig, effect_scale: float = 1.0, out_dir: Optional[Path] = None):
        self.config = config
        self.effect_scale = effect_scale
        self.out_dir = out_dir or GENERATED_DIR
        self.rng = np.random.Generator(np.random.PCG64(config.seed))

        # Load reference data
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            self.demo_seed = json.load(f)

        self.profiles = {}
        for p_file in PROFILES_DIR.glob("*.json"):
            with open(p_file, "r", encoding="utf-8") as pf:
                data = json.load(pf)
                self.profiles[data["profile_id"]] = data

        # Precompute working dates (72 working days ending on anchor date 2026-09-22)
        # Sunday is non-working day
        self.working_dates = self._compute_working_dates(config.anchor_date, config.num_weeks * config.working_days_per_week)

        # Entity collections
        self.sites = self.demo_seed.get("sites", [])
        self.zones = self.demo_seed.get("zones", [])
        self.operators = self.demo_seed.get("operators", [])
        self.all_machines = self.demo_seed.get("machines", [])
        self.detailed_machines = [m for m in self.all_machines if m.get("detail_level") == "detailed"]
        # Wheel loaders have NO generated tasks/idles/summaries (F16-R4)
        self.operational_machines = [
            m for m in self.detailed_machines if m.get("machine_class") in ("excavator", "haul_truck")
        ]

        # Persistent latent effects
        self.site_effects = {
            s["site_id"]: float(self.rng.normal(0, config.effects.get("site_variance", {}).get("sigma", 0.04)))
            for s in self.sites
        }
        self.operator_effects = {
            o["operator_id"]: float(self.rng.normal(0, config.effects.get("operator_variance", {}).get("sigma", 0.06)))
            for o in self.operators
        }

        # Select 6 operators with habitual unexplained idle habit
        working_op_ids = [
            o["operator_id"] for o in self.operators
            if o.get("regular_machine_class") in ("excavator", "haul_truck") and o["operator_id"] != "OP-0007"
        ]
        self.habitual_unexplained_ops = set(self.rng.choice(working_op_ids, size=6, replace=False))

        # Select 3 habitual overspeed haul truck operators
        ht_op_ids = [o["operator_id"] for o in self.operators if o.get("regular_machine_class") == "haul_truck"]
        self.habitual_overspeed_ops = set(self.rng.choice(ht_op_ids, size=3, replace=False))

        # Fixed synthetic device UUID per machine
        self.device_ids = {
            m["machine_id"]: deterministic_uuid(self.rng, f"dev:{m['machine_id']}")
            for m in self.all_machines
        }


    def _compute_working_dates(self, anchor_date_str: str, total_days: int) -> List[datetime]:
        """Calculates total_days working dates (skipping Sundays) ending on anchor_date."""
        anchor_dt = datetime.strptime(anchor_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        dates = []
        curr = anchor_dt
        while len(dates) < total_days:
            # Monday=0, Sunday=6
            if curr.weekday() != 6:
                dates.append(curr)
            curr -= timedelta(days=1)
        dates.reverse()
        return dates

    def generate_all(self) -> Dict[str, int]:
        """Generates all 13 bundle files."""
        self.out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Reference files
        sites_rows = self._generate_sites()
        zones_rows = self._generate_zones()
        operators_rows = self._generate_operators()
        machines_rows = self._generate_machines()
        fleet_rows = self._generate_fleet()

        # 2. Hourly conditions
        conditions_rows = self._generate_conditions()
        conditions_map = {f"{c['site_id']}:{c['valid_from']}": c for c in conditions_rows}

        # 3. Operational timeline: shifts, tasks, idles, alerts, summaries, ledger
        timeline_data = self._generate_timeline(conditions_map)

        shifts_rows = timeline_data["shifts"]
        tasks_rows = timeline_data["tasks"]
        idle_rows = timeline_data["idle_events"]
        alerts_rows = timeline_data["alerts"]
        summaries_rows = timeline_data["summaries_5m"]
        ledger_rows = timeline_data["ledger_entries"]

        # Sort all tables according to schema (ascending by grain time, then by ID)
        sites_rows.sort(key=lambda r: (r["created_at"], r["site_id"]))
        zones_rows.sort(key=lambda r: (r["created_at"], r["zone_id"]))
        operators_rows.sort(key=lambda r: (r["created_at"], r["operator_id"]))
        machines_rows.sort(key=lambda r: (r["created_at"], r["machine_id"]))
        fleet_rows.sort(key=lambda r: (r["status_observed_at"], r["machine_id"]))
        conditions_rows.sort(key=lambda r: (r["valid_from"], r["condition_id"]))
        shifts_rows.sort(key=lambda r: (r["started_at"], r["shift_id"]))
        tasks_rows.sort(key=lambda r: (r["planned_date"], r["machine_id"], r["sequence"]))
        idle_rows.sort(key=lambda r: (r["started_at"], r["idle_event_id"]))
        alerts_rows.sort(key=lambda r: (r["observed_at"], r["alert_event_id"]))
        summaries_rows.sort(key=lambda r: (r["window_start"], r["summary_id"]))
        ledger_rows.sort(key=lambda r: (r["observed_at"], r["entry_id"]))

        # Write CSVs and JSONL
        counts = {}
        counts["sites.csv"] = self._write_csv("sites.csv", sites_rows)
        counts["zones.csv"] = self._write_csv("zones.csv", zones_rows)
        counts["operators.csv"] = self._write_csv("operators.csv", operators_rows)
        counts["machines.csv"] = self._write_csv("machines.csv", machines_rows)
        counts["fleet.csv"] = self._write_csv("fleet.csv", fleet_rows)
        counts["shifts.csv"] = self._write_csv("shifts.csv", shifts_rows)
        counts["tasks.csv"] = self._write_csv("tasks.csv", tasks_rows)
        counts["conditions_hourly.csv"] = self._write_csv("conditions_hourly.csv", conditions_rows)
        counts["summaries_5m.csv"] = self._write_csv("summaries_5m.csv", summaries_rows)
        counts["idle_events.csv"] = self._write_csv("idle_events.csv", idle_rows)
        counts["alerts.csv"] = self._write_csv("alerts.csv", alerts_rows)
        counts["ledger_entries.jsonl"] = self._write_jsonl("ledger_entries.jsonl", ledger_rows)

        # Assumptions document & sha256
        assumptions_hash = generate_assumptions_doc(self.config, ASSUMPTIONS_PATH)

        # Build Manifest
        manifest_files = []
        grains = {
            "sites.csv": "site",
            "zones.csv": "site zone",
            "operators.csv": "fictional operator",
            "machines.csv": "detailed machine",
            "fleet.csv": "machine status snapshot",
            "shifts.csv": "operator-machine shift",
            "tasks.csv": "assigned task and final outcome",
            "conditions_hourly.csv": "site forecast valid hour",
            "summaries_5m.csv": "machine five-minute window",
            "idle_events.csv": "complete or open idle interval",
            "alerts.csv": "one alert lifecycle transition",
            "ledger_entries.jsonl": "one append-only ledger entry",
        }

        for filename, row_count in counts.items():
            fpath = self.out_dir / filename
            manifest_files.append({
                "path": filename,
                "rows": row_count,
                "sha256": compute_file_sha256(fpath),
                "grain": grains.get(filename, ""),
            })

        manifest = {
            "schema_version": self.config.schema_version,
            "generator_version": self.config.generator_version,
            "seed": self.config.seed,
            "anchor_date": self.config.anchor_date,
            "generated_at": "2026-09-22T23:59:59.000Z",  # Deterministic generation time
            "data_origin": self.config.data_origin,
            "profile_versions": {p["profile_id"]: p["version"] for p in self.profiles.values()},
            "files": manifest_files,
            "split_policy": self.config.split_policy,
            "assumptions_sha256": assumptions_hash,
            "limitations": "Synthetic data for prototype demonstration and offline evaluation only. Not representative of actual machine telemetry.",
        }

        manifest_path = self.out_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return counts

    def _write_csv(self, filename: str, rows: List[Dict[str, Any]]) -> int:
        if not rows:
            return 0
        path = self.out_dir / filename
        from shiftmate_ml.datagen.validate import EXPECTED_COLUMNS
        fieldnames = EXPECTED_COLUMNS.get(filename) or list(rows[0].keys())
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            for r in rows:
                clean_r = {}
                for k, v in r.items():
                    if v is None:
                        clean_r[k] = ""
                    elif isinstance(v, bool):
                        clean_r[k] = "true" if v else "false"
                    elif isinstance(v, (int, float)):
                        clean_r[k] = str(v)
                    else:
                        clean_r[k] = str(v)
                writer.writerow(clean_r)
        return len(rows)

    def _write_jsonl(self, filename: str, rows: List[Dict[str, Any]]) -> int:
        path = self.out_dir / filename
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, separators=(",", ":")) + "\n")
        return len(rows)

    def _generate_sites(self) -> List[Dict[str, Any]]:
        rows = []
        for s in self.sites:
            rows.append({
                "site_id": s["site_id"],
                "name": s["name"],
                "sector": s["sector"],
                "lat": s["lat"],
                "lon": s["lon"],
                "utc_offset_minutes": s["utc_offset_minutes"],
                "diesel_price_inr_per_l": s.get("diesel_price_inr_per_l", 92.5),
                "dark_start_local": s.get("dark_start_local", "18:30"),
                "dark_end_local": s.get("dark_end_local", "06:00"),
                "job_efficiency_override": s.get("job_efficiency_override"),
                "congestion_level": s.get("congestion_level", "medium"),
                "data_origin": "demo_seed",
                "created_at": "2026-06-01T00:00:00.000Z",
            })
        return rows

    def _generate_zones(self) -> List[Dict[str, Any]]:
        rows = []
        for z in self.zones:
            rows.append({
                "zone_id": z["zone_id"],
                "site_id": z["site_id"],
                "name": z["name"],
                "kind": z["kind"],
                "center_lat": z["center_lat"],
                "center_lon": z["center_lon"],
                "radius_m": z["radius_m"],
                "speed_limit_kmh": z.get("speed_limit_kmh"),
                "data_origin": "demo_seed",
                "created_at": "2026-06-01T00:00:00.000Z",
            })
        return rows

    def _generate_operators(self) -> List[Dict[str, Any]]:
        rows = []
        for o in self.operators:
            rows.append({
                "operator_id": o["operator_id"],
                "site_id": o["site_id"],
                "display_name": o["display_name"],
                "language": o["language"],
                "skill_level": o["skill_level"],
                "experience_months": o["experience_months"],
                "hired_at": o["hired_at"],
                "regular_machine_class": o["regular_machine_class"],
                "data_origin": "demo_seed",
                "created_at": "2026-06-01T00:00:00.000Z",
            })
        return rows

    def _generate_machines(self) -> List[Dict[str, Any]]:
        rows = []
        for m in self.detailed_machines:
            rows.append({
                "machine_id": m["machine_id"],
                "short_id": m["short_id"],
                "site_id": m["site_id"],
                "profile_id": m["profile_id"],
                "profile_version": m.get("profile_version", 1),
                "machine_class": m["machine_class"],
                "model_name": m["model_name"],
                "year_of_manufacture": m.get("year_of_manufacture", 2021),
                "detail_level": "detailed",
                "data_origin": "demo_seed",
                "created_at": "2026-06-01T00:00:00.000Z",
            })
        return rows

    def _generate_fleet(self) -> List[Dict[str, Any]]:
        rows = []
        for m in self.all_machines:
            rows.append({
                "machine_id": m["machine_id"],
                "short_id": m["short_id"],
                "site_id": m["site_id"],
                "machine_class": m.get("machine_class", "excavator"),
                "profile_id": m.get("profile_id", "excavator_20t"),
                "profile_version": m.get("profile_version", 1),
                "state": "READY",
                "open_alerts": 0,
                "status_observed_at": "2026-09-22T18:00:00.000Z",
                "last_sync_at": "2026-09-22T18:00:00.000Z",
                "detail_level": m.get("detail_level", "status_only"),
                "data_origin": self.config.data_origin,
            })
        return rows

    def _generate_conditions(self) -> List[Dict[str, Any]]:
        """Hourly forecasts per site (issued 18:00 site-local the day before) plus one congestion level
        per site and day. Forecast hours are aligned to site-local hours."""
        from shiftmate_ml.datagen.timeline import visibility_band

        rows = []
        self.day_congestion: Dict[Tuple[str, str], str] = {}
        for site in self.sites:
            site_id = site["site_id"]
            utc_offset = site["utc_offset_minutes"]
            is_mining = site["sector"] == "mining"
            first, last = self.working_dates[0], self.working_dates[-1] + timedelta(days=1)
            calendar = [first + timedelta(days=i) for i in range((last - first).days + 1)]
            for date in calendar:
                prev_date = date - timedelta(days=1)
                issued_local = datetime(prev_date.year, prev_date.month, prev_date.day, 18, 0, 0, tzinfo=timezone.utc)
                issued_at_str = iso_utc(issued_local - timedelta(minutes=utc_offset))
                cong_p = [0.1, 0.4, 0.5] if is_mining else [0.3, 0.5, 0.2]
                self.day_congestion[(site_id, date.strftime("%Y-%m-%d"))] = str(
                    self.rng.choice(["low", "medium", "high"], p=cong_p))

                for h in range(24):
                    valid_from_local = datetime(date.year, date.month, date.day, h, 0, 0, tzinfo=timezone.utc)
                    valid_from_utc = valid_from_local - timedelta(minutes=utc_offset)
                    valid_to_utc = valid_from_utc + timedelta(hours=1)

                    if is_mining:
                        wx = self.rng.choice(["clear", "dusty", "rain", "windy"], p=[0.55, 0.30, 0.10, 0.05])
                    elif h >= 14 and site_id == "SITE-CHN-01":
                        wx = self.rng.choice(["clear", "rain", "windy", "foggy"], p=[0.60, 0.25, 0.10, 0.05])
                    else:
                        wx = self.rng.choice(["clear", "rain", "windy", "foggy"], p=[0.80, 0.12, 0.05, 0.03])
                    wx = str(wx)

                    if wx == "foggy":
                        vis_m = float(self.rng.uniform(400, 950))
                    elif wx == "rain":
                        vis_m = float(self.rng.uniform(1200, 3500)) if self.rng.random() < 0.75 else float(self.rng.uniform(600, 950))
                    elif wx == "dusty":
                        vis_m = float(self.rng.uniform(1500, 4500)) if self.rng.random() < 0.8 else float(self.rng.uniform(700, 990))
                    else:
                        vis_m = float(self.rng.uniform(6000, 12000))

                    base_temp = 32.0 if is_mining else 28.0
                    temp_c = round(base_temp + 6.0 * math.sin((h - 8) / 24.0 * 2 * math.pi)
                                   + float(self.rng.normal(0, 1.5)), 1)
                    heat_index_c = round(temp_c + (2.0 if temp_c > 30 else 0.0), 1) if self.rng.random() > 0.02 else None
                    precip = round(float(self.rng.uniform(2.0, 18.0)), 1) if wx == "rain" else 0.0
                    wind_kmh = round(float(self.rng.uniform(40.0, 52.0)) if wx == "windy" else float(self.rng.uniform(6.0, 22.0)), 1)

                    rows.append({
                        "condition_id": f"{site_id}:{iso_utc(valid_from_utc)}",
                        "site_id": site_id,
                        "valid_from": iso_utc(valid_from_utc),
                        "valid_to": iso_utc(valid_to_utc),
                        "issued_at": issued_at_str,
                        "weather": wx,
                        "visibility": visibility_band(vis_m, False),
                        "visibility_m": round(vis_m, 1),
                        "temp_c": temp_c,
                        "heat_index_c": heat_index_c,
                        "wind_kmh": wind_kmh,
                        "precipitation_mm": precip,
                        "source": "seed",
                        "data_origin": self.config.data_origin,
                        "recorded_at": issued_at_str,
                    })
        return rows

    def _generate_timeline(self, conditions_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        from shiftmate_ml.datagen.timeline import TimelineBuilder

        return TimelineBuilder(self, conditions_map).build()


def run_generator(config_path: Optional[Path] = None, effect_scale: float = 1.0, out_dir: Optional[Path] = None):
    cfg = load_config(config_path)
    target_dir = out_dir
    if target_dir is None:
        if effect_scale == 1.0:
            target_dir = GENERATED_DIR
        else:
            target_dir = GENERATED_DIR / f"sens_{effect_scale}"

    print(f"Generating synthetic dataset (generator={cfg.generator_version}, seed={cfg.seed}, scale={effect_scale})...")
    print(f"Output directory: {target_dir}")

    gen = SyntheticGenerator(cfg, effect_scale=effect_scale, out_dir=target_dir)
    counts = gen.generate_all()

    print(f"Successfully generated {len(counts)} bundle files:")
    for fn, count in counts.items():
        print(f"  - {fn}: {count} records")

    # Export demo_history.json if baseline run (scale 1.0)
    if effect_scale == 1.0:
        ledger_path = target_dir / "ledger_entries.jsonl"
        ledger_entries = []
        with open(ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    ledger_entries.append(json.loads(line))

        demo_history_count = export_demo_history(ledger_entries, cfg.anchor_date)
        print(f"Exported demo_history.json: {demo_history_count} entries for EX-07, HT-03")

    return counts


def main():
    parser = argparse.ArgumentParser(description="Throughline Synthetic Dataset Generator")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="Path to config.yaml")
    parser.add_argument("--effect-scale", type=float, default=1.0, help="Effect scale factor (default 1.0, e.g. 0.5 or 1.5)")
    parser.add_argument("--all-sensitivities", action="store_true", help="Generate baseline and all sensitivity runs (0.5, 1.5)")
    parser.add_argument("--no-validate", action="store_true", help="Skip running validation gates after generation")
    args = parser.parse_args()

    # Generate baseline
    run_generator(args.config, effect_scale=args.effect_scale)

    if args.all_sensitivities:
        for scale in [0.5, 1.5]:
            run_generator(args.config, effect_scale=scale)

    if not args.no_validate:
        from shiftmate_ml.datagen.validate import validate_generated_bundle
        print("\nRunning DATASET_SCHEMA §5 validation gates...")
        success, report = validate_generated_bundle(GENERATED_DIR)
        print(report)
        if not success:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
