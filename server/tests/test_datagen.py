import json

from shiftmate_ml.datagen.effects import compute_baseline_minutes
from shiftmate_ml.datagen.validate import validate_generated_bundle
from shiftmate_ml.paths import DEMO_HISTORY_PATH, GENERATED_DIR, PROFILES_DIR


def test_baseline_calculation_tc09():
    """Verify baseline formulas against technical spec §8.6.1 and TC-09."""
    with open(PROFILES_DIR / "excavator_20t.v1.json", "r", encoding="utf-8") as f:
        ex_prof = json.load(f)
    with open(PROFILES_DIR / "haul_truck_90t.v1.json", "r", encoding="utf-8") as f:
        ht_prof = json.load(f)

    # 1. Trenching 40 m clay -> 49.7 min (±0.1)
    b1 = compute_baseline_minutes(ex_prof, "trenching", "clay", 40.0)
    assert abs(b1 - 49.7) < 0.1, f"Expected 49.7, got {b1}"

    # 2. Truck loading 60 m3 clay -> 28.5 min (±0.1)
    b2 = compute_baseline_minutes(ex_prof, "truck_loading", "clay", 60.0)
    assert abs(b2 - 28.5) < 0.1, f"Expected 28.5, got {b2}"

    # 3. Haul 1600 t overburden -> 256.0 min (±0.1)
    b3 = compute_baseline_minutes(ht_prof, "haul_overburden", "overburden", 1600.0)
    assert abs(b3 - 256.0) < 0.1, f"Expected 256.0, got {b3}"


def test_validation_gates_baseline():
    """Verify all 8 gates pass on the generated baseline bundle."""
    success, report = validate_generated_bundle(GENERATED_DIR)
    assert success, f"Validation gates failed:\n{report}"


def test_validation_gates_sensitivity():
    """Verify all 8 gates pass on sensitivity bundles."""
    s_05 = GENERATED_DIR / "sens_0.5"
    if s_05.exists():
        success, report = validate_generated_bundle(s_05)
        assert success, f"sens_0.5 failed:\n{report}"

    s_15 = GENERATED_DIR / "sens_1.5"
    if s_15.exists():
        success, report = validate_generated_bundle(s_15)
        assert success, f"sens_1.5 failed:\n{report}"


def test_demo_history_export():
    """Verify demo_history.json constraints."""
    assert DEMO_HISTORY_PATH.exists()
    with open(DEMO_HISTORY_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)

    assert len(entries) > 0
    # Check that machines are EX-07 and HT-03
    machines = {e.get("machine_id") for e in entries}
    assert machines.issubset({"EX-07", "HT-03"})

    # Check that every entry has day_offset
    assert all("day_offset" in e for e in entries)

    # In tasks.csv, OP-0007 has exactly 1 completed trenching task and 0 in rain/dust/darkness
    import csv

    with open(GENERATED_DIR / "tasks.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        op_0007_tasks = [r for r in reader if r["operator_id"] == "OP-0007"]

    trenching_tasks = [r for r in op_0007_tasks if r["task_type"] == "trenching"]
    assert len(trenching_tasks) == 1

    adverse_weather_tasks = [
        r
        for r in op_0007_tasks
        if r["weather_at_start"] in ("rain", "dusty") or r["darkness_at_start"] == "true"
    ]
    assert len(adverse_weather_tasks) == 0
