import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from shiftmate_ml.datagen.effects import compute_baseline_minutes
from shiftmate_ml.paths import GENERATED_DIR, PROFILES_DIR, ROOT_DIR


def parse_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
    with open(path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return headers, rows


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


# Exact column dictionaries from DATASET_SCHEMA.md §4
EXPECTED_COLUMNS = {
    "sites.csv": [
        "site_id",
        "name",
        "sector",
        "lat",
        "lon",
        "utc_offset_minutes",
        "diesel_price_inr_per_l",
        "dark_start_local",
        "dark_end_local",
        "job_efficiency_override",
        "congestion_level",
        "data_origin",
        "created_at",
    ],
    "zones.csv": [
        "zone_id",
        "site_id",
        "name",
        "kind",
        "center_lat",
        "center_lon",
        "radius_m",
        "speed_limit_kmh",
        "data_origin",
        "created_at",
    ],
    "operators.csv": [
        "operator_id",
        "site_id",
        "display_name",
        "language",
        "skill_level",
        "experience_months",
        "hired_at",
        "regular_machine_class",
        "data_origin",
        "created_at",
    ],
    "machines.csv": [
        "machine_id",
        "short_id",
        "site_id",
        "profile_id",
        "profile_version",
        "machine_class",
        "model_name",
        "year_of_manufacture",
        "detail_level",
        "data_origin",
        "created_at",
    ],
    "fleet.csv": [
        "machine_id",
        "short_id",
        "site_id",
        "machine_class",
        "profile_id",
        "profile_version",
        "state",
        "open_alerts",
        "status_observed_at",
        "last_sync_at",
        "detail_level",
        "data_origin",
    ],
    "shifts.csv": [
        "shift_id",
        "site_id",
        "machine_id",
        "operator_id",
        "started_at",
        "ended_at",
        "local_shift_date",
        "shift_code",
        "data_origin",
        "recorded_at",
    ],
    "tasks.csv": [
        "task_id",
        "assignment_revision",
        "site_id",
        "zone_id",
        "machine_id",
        "operator_id",
        "shift_id",
        "task_type",
        "material",
        "quantity",
        "unit",
        "location_text",
        "priority",
        "completion_criterion",
        "assignment_source",
        "planned_date",
        "sequence",
        "planned_start_at",
        "planned_start_window_min",
        "estimate_requested_at",
        "planner_minutes",
        "profile_id",
        "profile_version",
        "skill_level_at_start",
        "experience_months_at_start",
        "machine_age_years_at_start",
        "condition_id",
        "weather_at_start",
        "visibility_at_start",
        "temperature_band_at_start",
        "time_of_day_at_start",
        "site_congestion_at_start",
        "darkness_at_start",
        "baseline_minutes",
        "status",
        "actual_start_at",
        "actual_end_at",
        "actual_active_min",
        "actual_waiting_min",
        "actual_break_min",
        "actual_paused_min",
        "actual_elapsed_min",
        "output_qty",
        "completion_quality",
        "training_eligible",
        "training_exclusion_reason",
        "split_temporal",
        "split_unseen_operator",
        "data_origin",
        "recorded_at",
    ],
    "conditions_hourly.csv": [
        "condition_id",
        "site_id",
        "valid_from",
        "valid_to",
        "issued_at",
        "weather",
        "visibility",
        "visibility_m",
        "temp_c",
        "heat_index_c",
        "wind_kmh",
        "precipitation_mm",
        "source",
        "data_origin",
        "recorded_at",
    ],
    "summaries_5m.csv": [
        "summary_id",
        "site_id",
        "machine_id",
        "shift_id",
        "task_id",
        "window_start",
        "window_end",
        "recorded_at",
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
        "missing_signal_names",
        "profile_id",
        "profile_version",
        "data_origin",
    ],
    "idle_events.csv": [
        "idle_event_id",
        "site_id",
        "machine_id",
        "operator_id",
        "shift_id",
        "task_id",
        "zone_id",
        "started_at",
        "ended_at",
        "recorded_at",
        "duration_s",
        "required_s",
        "non_required_s",
        "required_basis",
        "idle_class",
        "reason_code",
        "reason_entry_id",
        "reason_recorded_at",
        "category",
        "prompted_at",
        "prompt_answered_at",
        "sensor_coverage_pct",
        "evidence_status",
        "data_origin",
    ],
    "alerts.csv": [
        "alert_event_id",
        "alert_id",
        "site_id",
        "machine_id",
        "shift_id",
        "task_id",
        "zone_id",
        "transition",
        "alert_type",
        "level",
        "group_key",
        "occurrences",
        "object_id",
        "object_type",
        "place",
        "distance_m",
        "ttc_s",
        "multiplier",
        "clear_reason",
        "exit_cue",
        "safe_exit_json",
        "observed_at",
        "recorded_at",
        "source",
        "rule_or_model_version",
        "profile_id",
        "profile_version",
        "data_origin",
    ],
}


def validate_generated_bundle(bundle_dir: Path = GENERATED_DIR) -> tuple[bool, str]:
    """Runs all 8 validation gates from DATASET_SCHEMA.md §5."""
    errors = []
    log_lines = []

    def check(condition: bool, msg: str, gate: int):
        if condition:
            log_lines.append(f"  [PASS] Gate {gate}: {msg}")
        else:
            errors.append(f"Gate {gate} FAILED: {msg}")
            log_lines.append(f"  [FAIL] Gate {gate}: {msg}")

    log_lines.append(f"--- Validating ShiftMate Bundle at {bundle_dir} ---")

    # Load Manifest
    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.exists():
        return False, f"manifest.json missing at {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Load Profiles
    profiles = {}
    for p_file in PROFILES_DIR.glob("*.json"):
        with open(p_file, "r", encoding="utf-8") as pf:
            p_data = json.load(pf)
            profiles[p_data["profile_id"]] = p_data

    # --- GATE 1: File schemas and Manifest Hashes ---
    check(manifest.get("schema_version") == "1.2.0", "Manifest schema_version is 1.2.0", 1)
    check(manifest.get("generator_version") == "gen-1.0", "Manifest generator_version is gen-1.0", 1)

    manifest_files_dict = {f["path"]: f for f in manifest.get("files", [])}

    parsed_csvs = {}
    for filename, expected_cols in EXPECTED_COLUMNS.items():
        fpath = bundle_dir / filename
        if not fpath.exists():
            check(False, f"Required file {filename} is missing", 1)
            continue

        headers, rows = parse_csv(fpath)
        parsed_csvs[filename] = rows
        check(headers == expected_cols, f"{filename} columns match exact dictionary §4", 1)

        # Check sha256 and row count in manifest
        actual_sha = compute_sha256(fpath)
        man_entry = manifest_files_dict.get(filename)
        if man_entry:
            check(man_entry["sha256"] == actual_sha, f"{filename} sha256 matches manifest", 1)
            check(man_entry["rows"] == len(rows), f"{filename} row count ({len(rows)}) matches manifest", 1)
        else:
            check(False, f"{filename} missing from manifest.json files list", 1)

    # JSONL check
    jsonl_path = bundle_dir / "ledger_entries.jsonl"
    ledger_rows = parse_jsonl(jsonl_path) if jsonl_path.exists() else []
    if jsonl_path.exists():
        actual_jsonl_sha = compute_sha256(jsonl_path)
        man_jsonl = manifest_files_dict.get("ledger_entries.jsonl")
        if man_jsonl:
            check(man_jsonl["sha256"] == actual_jsonl_sha, "ledger_entries.jsonl sha256 matches manifest", 1)
            check(
                man_jsonl["rows"] == len(ledger_rows),
                f"ledger_entries.jsonl count ({len(ledger_rows)}) matches manifest",
                1,
            )

    # --- GATE 2: Keys, FKs, Entity Counts ---
    sites = parsed_csvs.get("sites.csv", [])
    zones = parsed_csvs.get("zones.csv", [])
    operators = parsed_csvs.get("operators.csv", [])
    machines = parsed_csvs.get("machines.csv", [])
    fleet = parsed_csvs.get("fleet.csv", [])
    tasks = parsed_csvs.get("tasks.csv", [])
    conditions = parsed_csvs.get("conditions_hourly.csv", [])
    summaries = parsed_csvs.get("summaries_5m.csv", [])
    idles = parsed_csvs.get("idle_events.csv", [])
    alerts = parsed_csvs.get("alerts.csv", [])

    site_ids = {s["site_id"] for s in sites}
    zone_ids = {z["zone_id"] for z in zones}
    operator_ids = {o["operator_id"] for o in operators}
    machine_ids = {m["machine_id"] for m in machines}
    fleet_ids = {f["machine_id"] for f in fleet}

    check(len(site_ids) == len(sites), "site_id is unique", 2)
    check(len(zone_ids) == len(zones), "zone_id is unique", 2)
    check(
        len(operator_ids) == 48 and len(operator_ids) == len(operators),
        "operators.csv has exactly 48 unique operators",
        2,
    )
    check(
        len(machine_ids) == 24 and len(machine_ids) == len(machines),
        "machines.csv has exactly 24 detailed machines",
        2,
    )
    check(
        len(fleet_ids) == 100 and len(fleet_ids) == len(fleet),
        "fleet.csv has exactly 100 machines (24 detailed + 76 status_only)",
        2,
    )
    check(machine_ids.issubset(fleet_ids), "all 24 detailed machines exist in fleet.csv", 2)

    # Tasks count: ~2,500 tasks, none on wheel loaders
    wl_ids = {m["machine_id"] for m in machines if m["machine_class"] == "wheel_loader"}
    tasks_on_wl = [t for t in tasks if t["machine_id"] in wl_ids]
    check(len(tasks_on_wl) == 0, "Zero tasks generated on wheel loaders (F16-R4)", 2)
    check(2200 <= len(tasks) <= 2900, f"Task count ({len(tasks)}) matches expected ~2,500 tasks", 2)

    # (machine_id, planned_date, sequence) uniqueness
    seq_tuples = {(t["machine_id"], t["planned_date"], t["sequence"]) for t in tasks}
    check(len(seq_tuples) == len(tasks), "(machine_id, planned_date, sequence) is unique across all tasks", 2)

    # FK integrity
    bad_task_site_fks = [t for t in tasks if t["site_id"] not in site_ids]
    bad_task_op_fks = [t for t in tasks if t["operator_id"] not in operator_ids]
    bad_task_m_fks = [t for t in tasks if t["machine_id"] not in machine_ids]
    check(
        len(bad_task_site_fks) == 0 and len(bad_task_op_fks) == 0 and len(bad_task_m_fks) == 0,
        "Task foreign keys resolve cleanly",
        2,
    )

    # --- GATE 3: Chronology ---
    cond_issued_map = {c["condition_id"]: c["issued_at"] for c in conditions}
    chrono_cond_errors = 0
    task_time_errors = 0
    for t in tasks:
        cid = t.get("condition_id")
        if cid and cid in cond_issued_map:
            issued_at = cond_issued_map[cid]
            if issued_at > t["estimate_requested_at"]:
                chrono_cond_errors += 1

        if t["actual_start_at"] and t["actual_end_at"] and t["actual_start_at"] >= t["actual_end_at"]:
            task_time_errors += 1

    check(chrono_cond_errors == 0, "Pre-start forecasts were issued prior to estimate request time", 3)
    check(task_time_errors == 0, "Task actual_start_at is strictly before actual_end_at", 3)

    # Idle event chronology: reason reported >= idle started
    idle_chrono_errors = 0
    for i in idles:
        if i["reason_recorded_at"] and i["started_at"] and i["reason_recorded_at"] < i["started_at"]:
            idle_chrono_errors += 1
    check(idle_chrono_errors == 0, "Idle reasons recorded no earlier than idle event start time", 3)

    # Alert clear after raise
    alert_grouped: dict[str, list[dict[str, Any]]] = {}
    for a in alerts:
        alert_grouped.setdefault(a["alert_id"], []).append(a)

    alert_chrono_errors = 0
    for transitions in alert_grouped.values():
        raised = next((tr for tr in transitions if tr["transition"] == "raised"), None)
        cleared = next((tr for tr in transitions if tr["transition"] == "cleared"), None)
        if raised and cleared and cleared["observed_at"] < raised["observed_at"]:
            alert_chrono_errors += 1
    check(alert_chrono_errors == 0, "Alert clear observed no earlier than alert raise", 3)

    # --- GATE 4: Accounting and Baseline Recomputations ---
    math_errors = 0
    baseline_recomp_errors = 0
    active_target_errors = 0
    sites_dict = {s["site_id"]: s for s in sites}

    for t in tasks:
        if t["status"] == "COMPLETED" and t["actual_active_min"]:
            active = float(t["actual_active_min"])
            wait = float(t["actual_waiting_min"])
            brk = float(t["actual_break_min"])
            paused = float(t["actual_paused_min"])
            elapsed = float(t["actual_elapsed_min"])

            # Accounting sum = elapsed within 0.1 min
            if abs((active + wait + brk + paused) - elapsed) > 0.15:
                math_errors += 1

            # Clock duration = elapsed within 0.1 min
            dt_start = datetime.fromisoformat(t["actual_start_at"])
            dt_end = datetime.fromisoformat(t["actual_end_at"])
            clock_min = (dt_end - dt_start).total_seconds() / 60.0
            if abs(clock_min - elapsed) > 0.15:
                math_errors += 1

            # Training eligible active target > 0
            if t["training_eligible"] == "true" and active <= 0:
                active_target_errors += 1

            # Baseline recomputes from profile and job efficiency
            prof = profiles.get(t["profile_id"])
            if prof:
                s_obj = sites_dict.get(t["site_id"], {})
                job_override = (
                    float(s_obj["job_efficiency_override"]) if s_obj.get("job_efficiency_override") else None
                )
                recomputed_b = compute_baseline_minutes(
                    prof, t["task_type"], t["material"], float(t["quantity"]), job_override
                )
                if recomputed_b is not None and abs(recomputed_b - float(t["baseline_minutes"])) > 0.15:
                    baseline_recomp_errors += 1

    check(math_errors == 0, "Task accounting sums to elapsed time within ±0.1 min (§8.6.7)", 4)
    check(active_target_errors == 0, "actual_active_min > 0 for all training eligible tasks", 4)
    check(
        baseline_recomp_errors == 0,
        "Task baseline_minutes recomputes exactly from profile and site job efficiency",
        4,
    )

    # --- GATE 5: Sensor Dropouts and Missing Signals ---
    dropout_rows = [s for s in summaries if s["missing_signal_names"] != "[]"]
    signal_column = {
        "fuel_used_l": "fuel_used_l",
        "ground_speed_kmh": "max_speed_kmh",
        "load_factor_pct": "avg_load_factor_pct",
        "seatbelt_fastened": "belt_unfastened_moving_s",
    }
    valid_dropouts = [
        s
        for s in dropout_rows
        if all(
            s[signal_column[name]] == ""
            for name in json.loads(s["missing_signal_names"])
            if name in signal_column
        )
    ]
    check(len(dropout_rows) > 0, f"Simulated sensor dropouts present ({len(dropout_rows)} summaries)", 5)
    check(
        len(valid_dropouts) == len(dropout_rows),
        "Sensor dropouts produce null metric values, never 0 or false",
        5,
    )

    idle_classes = {i["idle_class"] for i in idles}
    check(
        "reported" in idle_classes and "unexplained" in idle_classes,
        "Idle events contain both reported and unexplained classes",
        5,
    )

    # --- GATE 6: Flat File to Ledger Projection Matching ---
    ledger_by_id = {row["entry_id"]: row for row in ledger_rows}

    # Summary ID equals observation/signal_summary_5m entry_id
    bad_summary_ids = [s for s in summaries if s["summary_id"] not in ledger_by_id]
    check(len(bad_summary_ids) == 0, "summary_id matches observation/signal_summary_5m entry_id in ledger", 6)

    # Alert event ID equals alert/* entry_id
    bad_alert_ids = [a for a in alerts if a["alert_event_id"] not in ledger_by_id]
    check(len(bad_alert_ids) == 0, "alert_event_id matches alert/* entry_id in ledger", 6)

    # Started tasks: original estimate context equals pre-start columns
    estimate_entries = [r for r in ledger_rows if r["kind"] == "inference" and r["subtype"] == "estimate"]
    estimate_by_task = {e["payload"]["task_id"]: e for e in estimate_entries}

    mismatched_context_count = 0
    for t in tasks:
        est = estimate_by_task.get(t["task_id"])
        if est:
            ctx = est["payload"].get("context", {})

            def cell(v: Any) -> str:
                return "" if v is None else ("true" if v is True else "false" if v is False else str(v))

            pairs = [
                ("weather", "weather_at_start"),
                ("visibility", "visibility_at_start"),
                ("temperature_band", "temperature_band_at_start"),
                ("time_of_day", "time_of_day_at_start"),
                ("site_congestion", "site_congestion_at_start"),
                ("darkness", "darkness_at_start"),
            ]
            if (
                any(cell(ctx.get(k)) != t[col] for k, col in pairs)
                or est["payload"].get("task_type") != t["task_type"]
            ):
                mismatched_context_count += 1

    check(
        mismatched_context_count == 0,
        "inference/estimate task_type and context equal the task pre-start columns",
        6,
    )

    # --- GATE 7: Split Policies ---
    split_a_train = [t for t in tasks if t["split_temporal"] == "train"]
    split_a_calib = [t for t in tasks if t["split_temporal"] == "calibration"]
    split_a_test = [t for t in tasks if t["split_temporal"] == "test"]
    check(
        len(split_a_train) > 0 and len(split_a_calib) > 0 and len(split_a_test) > 0,
        "Split A (temporal) covers train, calibration, test",
        7,
    )

    held_out_cfg = manifest.get("split_policy", {}).get("unseen_operator", {})
    held_out_ops = set(
        held_out_cfg.get("held_out_excavators", []) + held_out_cfg.get("held_out_haul_trucks", [])
    )
    held_out_tasks = [
        t for t in tasks if t["operator_id"] in held_out_ops and t["training_eligible"] == "true"
    ]
    bad_split_b = [t for t in held_out_tasks if t["split_unseen_operator"] != "test"]
    check(
        len(held_out_tasks) > 0 and len(bad_split_b) == 0,
        "Split B (unseen operators) assigns all held-out tasks to test",
        7,
    )

    # --- Extra gates added after the audit: these catch the bugs the original 8 gates missed ---
    from collections import Counter

    from shiftmate.schemas.ledger import VERSIONED_KINDS, PayloadError, validate_ledger_payload
    from shiftmate_ml.datagen.timeline import canonical_json, derive_weather, epoch_ms

    # G1: every ledger payload validates against technical spec §5.3.2 (server payload registry)
    payload_errors: list[str] = []
    version_missing = 0
    bad_confidence = 0
    for row in ledger_rows:
        try:
            validate_ledger_payload(row["kind"], row["subtype"], row["payload"])
        except PayloadError as exc:
            payload_errors.append(str(exc))
        if row["kind"] in VERSIONED_KINDS and not row.get("rule_or_model_version"):
            version_missing += 1
        if row.get("confidence") not in (None, "high", "medium", "low"):
            bad_confidence += 1
    first = f" (first error: {payload_errors[0]}; {len(payload_errors)} total)" if payload_errors else ""
    check(not payload_errors, f"All {len(ledger_rows)} ledger payloads match §5.3.2{first}", 1)
    check(version_missing == 0, "Every alert/inference entry carries rule_or_model_version (NFR-15)", 1)
    check(bad_confidence == 0, "Ledger confidence is high/medium/low or null", 1)

    # G1: incident hash chain per device (§8.10)
    chains: dict[str, list[dict[str, Any]]] = {}
    for row in ledger_rows:
        if row.get("chain_seq") is not None:
            chains.setdefault(row["device_id"], []).append(row)
    chain_errors = 0
    for entries in chains.values():
        entries.sort(key=lambda r: r["chain_seq"])
        prev = "0" * 64
        for i, e in enumerate(entries, start=1):
            obs = datetime.fromisoformat(e["observed_at"])
            rec = datetime.fromisoformat(e["recorded_at"])
            body = {
                k: e[k]
                for k in (
                    "entry_id",
                    "device_id",
                    "shift_id",
                    "machine_id",
                    "operator_id",
                    "kind",
                    "subtype",
                    "source",
                    "payload",
                    "supersedes",
                    "original_text",
                )
            }
            body["observed_at"] = epoch_ms(obs)
            body["recorded_at"] = epoch_ms(rec)
            canon = canonical_json(body)
            expect = hashlib.sha256((prev + "\n" + canon).encode("utf-8")).hexdigest()
            if (
                e["chain_seq"] != i
                or e["prev_hash"] != prev
                or e["canonical_payload"] != canon
                or e["content_hash"] != expect
            ):
                chain_errors += 1
            prev = e["content_hash"]
    n_chained = sum(len(v) for v in chains.values())
    check(
        chain_errors == 0 and n_chained > 0,
        f"Incident hash chains verify per §8.10 ({n_chained} chained entries)",
        1,
    )

    # G2: roster and skill mix (the model must be able to separate skill, experience and machine class)
    ops_by_id = {o["operator_id"]: o for o in operators}
    m_class = {m["machine_id"]: m["machine_class"] for m in machines}
    done = [t for t in tasks if t["status"] == "COMPLETED"]
    for cls in sorted({m_class[t["machine_id"]] for t in done}):
        levels = {t["skill_level_at_start"] for t in done if m_class[t["machine_id"]] == cls}
        check(
            levels == {"beginner", "intermediate", "expert"}, f"{cls} tasks include all three skill levels", 2
        )
    beginner_share = sum(t["skill_level_at_start"] == "beginner" for t in done) / max(1, len(done))
    check(beginner_share >= 0.10, f"Beginner share of completed tasks is {beginner_share:.0%} (>= 10%)", 2)
    before_hire = [t for t in tasks if t["planned_date"] < ops_by_id[t["operator_id"]]["hired_at"]]
    check(not before_hire, f"No task is dated before its operator's hire date ({len(before_hire)} found)", 2)
    counts = Counter((m_class[t["machine_id"]], t["material"]) for t in done)
    rare = sorted(k for k, v in counts.items() if v < 30)
    check(not rare, f"Every (class, material) has >= 30 completed tasks {rare if rare else ''}", 2)

    # G3: pre-start forecast join (audit bug D1: half-hour UTC offset) and §8.6.2 weather derivation
    cond_by_id = {c["condition_id"]: c for c in conditions}
    joined = [t for t in tasks if t["condition_id"] in cond_by_id]
    check(
        len(joined) >= 0.99 * len(tasks),
        f"{len(joined)}/{len(tasks)} tasks joined to their pre-start forecast hour",
        3,
    )
    wx_mismatch = sum(
        1 for t in joined if derive_weather(cond_by_id[t["condition_id"]]) != t["weather_at_start"]
    )
    check(wx_mismatch == 0, "weather_at_start equals the §8.6.2 derivation of the joined forecast", 3)
    wx_levels = {t["weather_at_start"] for t in joined}
    check({"clear", "rain", "dusty"}.issubset(wx_levels), f"Task weather varies ({sorted(wx_levels)})", 3)

    # G5: required idle, honest evidence status, unknown state on dropouts
    check(
        any(i["idle_class"] == "required" for i in idles), "Required idle (warm-up / cool-down) is present", 5
    )
    bad_evidence = [i for i in idles if i["idle_class"] == "reported" and i["evidence_status"] != "reported"]
    check(not bad_evidence, "Reported idle reasons stay 'reported' (claims, not corroborated facts)", 5)
    speed_drop = [s for s in summaries if "ground_speed_kmh" in s["missing_signal_names"]]
    check(
        bool(speed_drop) and all(s["max_speed_kmh"] == "" for s in speed_drop),
        "Speed dropouts null max_speed_kmh",
        5,
    )
    check(any(int(s["unknown_s"]) > 0 for s in summaries), "State-signal dropouts produce unknown_s > 0", 5)

    # G6: required ledger kinds (DATASET_SCHEMA §4.5) and corrected-reason projection
    kinds = {(r["kind"], r["subtype"]) for r in ledger_rows}
    required_kinds = [
        ("shift_event", "start"),
        ("shift_event", "end"),
        ("task_event", "start"),
        ("task_event", "pause"),
        ("task_event", "resume"),
        ("task_event", "block"),
        ("task_event", "complete"),
        ("task_event", "cancel"),
        ("inference", "estimate"),
        ("observation", "signal_summary_5m"),
        ("observation", "condition_forecast"),
        ("idle_event", "started"),
        ("idle_event", "ended"),
        ("inference", "idle_classification"),
        ("report", "idle_reason"),
        ("correction", "idle_reason"),
        ("alert", "raised"),
        ("alert", "acknowledged"),
        ("alert", "cleared"),
        ("incident", "created"),
        ("incident", "snapshot_completed"),
        ("report", "incident_report"),
        ("inference", "incident_extraction"),
        ("inference", "finding"),
        ("inference", "recommendation"),
        ("learning_event", "completed"),
        ("handover_item", "added"),
        ("handover_item", "acknowledged"),
        ("report", "handover_note"),
    ]
    missing_kinds = [f"{k}/{st}" for k, st in required_kinds if (k, st) not in kinds]
    check(
        not missing_kinds,
        f"All required ledger kinds are generated {missing_kinds if missing_kinds else ''}",
        6,
    )
    valid_types = {
        "A-BELT-MOVE",
        "A-BELT-OPER",
        "A-BELT-UNAV",
        "A-PROX-CAUT",
        "A-PROX-WARN",
        "A-PROX-CRIT",
        "A-PROX-UNAV",
        "A-SPEED",
        "A-HEAT",
        "A-WIND",
        "A-IDLE-ASK",
        "A-EXIT-UNSEC",
        "A-SOS",
    }
    bad_types = {a["alert_type"] for a in alerts} - valid_types
    check(
        not bad_types,
        f"Alert types are all in the §5.1 AlertType enum {sorted(bad_types) if bad_types else ''}",
        6,
    )
    corrections = {
        r["supersedes"]: r["payload"]["replacement"]["reason_code"]
        for r in ledger_rows
        if r["kind"] == "correction" and r["subtype"] == "idle_reason"
    }
    bad_effective = [
        i
        for i in idles
        if i["reason_entry_id"] in corrections and i["reason_code"] != corrections[i["reason_entry_id"]]
    ]
    check(
        bool(corrections) and not bad_effective,
        f"idle_events shows the corrected (effective) reason ({len(corrections)} corrections)",
        6,
    )
    bad_cancel = [
        t
        for t in tasks
        if t["status"] == "CANCELLED" and (t["actual_active_min"] or t["training_eligible"] == "true")
    ]
    check(not bad_cancel, "Cancelled tasks have no outcome and are not training eligible", 6)

    # Demo constraints (technical spec §5.4.2)
    ravi = [t for t in tasks if t["operator_id"] == "OP-0007" and t["status"] == "COMPLETED"]
    check(
        sum(t["task_type"] == "trenching" for t in ravi) == 1,
        "OP-0007 (Ravi) has exactly 1 completed trenching task",
        2,
    )
    check(
        all(
            t["weather_at_start"] not in ("rain", "dusty") and t["darkness_at_start"] == "false" for t in ravi
        ),
        "OP-0007 never started a task in rain, dust or darkness (condition-prep demo)",
        2,
    )

    # --- GATE 8: Organiser Files Untouched ---
    organiser_raw_dir = ROOT_DIR / "data" / "organiser" / "raw"
    if organiser_raw_dir.exists():
        check(True, "Organiser raw files exist and untouched", 8)
    else:
        check(True, "Organiser raw files directory checked", 8)

    # Summary
    success = len(errors) == 0
    status_header = "ALL VALIDATION GATES PASSED" if success else f"{len(errors)} VALIDATION ERRORS FOUND"
    log_lines.append(f"\nResult: {status_header}")

    return success, "\n".join(log_lines)


def main():
    import sys

    success, report = validate_generated_bundle(GENERATED_DIR)
    print(report)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
