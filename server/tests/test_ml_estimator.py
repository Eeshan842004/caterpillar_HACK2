"""Estimator training, export and parity (T36, TC-63, §5.4.4, §8.6.2–§8.6.4)."""

import json
import re

import numpy as np
import pytest

from shiftmate_ml.paths import GENERATED_DIR, MODELS_DIR, PARITY_DIR
from shiftmate_ml.train import estimator as est
from shiftmate_ml.train import export

CLASSES = ["excavator", "haul_truck"]
REQUIRED_KEYS = {
    "artifact_id",
    "kind",
    "machine_class",
    "version",
    "trained_at",
    "data_origin",
    "target",
    "alpha",
    "categorical",
    "numeric",
    "coefficients",
    "intercept",
    "residual_quantiles",
    "task_type_counts",
    "min_task_type_count",
    "min_calibration_n",
    "fallback_band",
    "metrics",
}

needs_bundle = pytest.mark.skipif(
    not (GENERATED_DIR / "tasks.csv").exists(),
    reason="data/generated missing: run shiftmate_ml.datagen.generate",
)


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    out = tmp_path_factory.mktemp("models")
    export.main(
        ["--data-dir", str(GENERATED_DIR), "--models-dir", str(out), "--parity-dir", str(out / "parity")]
    )
    return out


def _artifact(directory, machine_class):
    return json.loads((directory / f"estimator.{machine_class}.v1.json").read_text(encoding="utf-8"))


def test_conformal_quantiles_follow_spec_indices():
    r = np.arange(1, 20, dtype=float)  # n = 19 → k_lo = 2, k_hi = 18
    q = est.conformal_quantiles(r[::-1])
    assert (q["n"], q["q_lo"], q["q_mid"], q["q_hi"]) == (19, 2.0, 10.0, 18.0)


def test_unknown_level_encodes_as_zeros():
    categorical = [{"name": "material", "group": "material", "levels": ["clay", "rock"], "reference": "clay"}]
    assert est.encode({"material": "basalt"}, categorical, []) == {"material=rock": 0.0}
    assert est.encode({"material": "rock"}, categorical, []) == {"material=rock": 1.0}


@needs_bundle
@pytest.mark.parametrize("machine_class", CLASSES)
def test_tc63_artifact_shape_and_calibration(trained, machine_class):
    art = _artifact(trained, machine_class)
    assert REQUIRED_KEYS <= art.keys()
    assert art["artifact_id"] == f"estimator.{machine_class}@1" and art["kind"] == "estimator"
    assert art["alpha"] in est.ALPHAS
    keys = set(est.column_keys(art["categorical"], art["numeric"]))
    assert set(art["coefficients"]) == keys
    for c in art["categorical"]:
        assert c["reference"] in c["levels"]
        assert f"{c['name']}={c['reference']}" not in art["coefficients"]
    assert all(re.fullmatch(r"[a-z_]+(=[a-z_]+)?", k) for k in keys)
    assert all(n["std"] > 0 for n in art["numeric"])
    for q in [art["residual_quantiles"]["pooled"], *art["residual_quantiles"]["by_task_type"].values()]:
        assert q["q_lo"] <= q["q_mid"] <= q["q_hi"]

    # Factors include weather and skill (B1 done-when)
    assert art["coefficients"]["weather=rain"] > 0.03
    assert art["coefficients"]["skill_level=beginner"] > 0.1

    # Calibration: split-A test P10–P90 coverage 0.80 ± 0.08
    tasks, machines, _ = export.load_bundle(GENERATED_DIR)
    rows = est.load_class_rows(tasks, machines, machine_class)
    test = rows[rows["split_temporal"] == "test"]
    pred = est.predict_rows(test, art)
    actual = test["actual_active_min"].to_numpy(float)
    coverage = float(np.mean((actual >= pred["p10_min"].to_numpy()) & (actual <= pred["p90_min"].to_numpy())))
    assert 0.72 <= coverage <= 0.88, coverage


@needs_bundle
@pytest.mark.parametrize("machine_class", CLASSES)
def test_committed_artifacts_match_training(trained, machine_class):
    """The bundled artifact and golden file are exactly what training produces from the current bundle."""
    assert _artifact(MODELS_DIR, machine_class) == _artifact(trained, machine_class)
    name = f"estimator.{machine_class}.golden.json"
    assert json.loads((PARITY_DIR / name).read_text("utf-8")) == json.loads(
        (trained / "parity" / name).read_text("utf-8")
    )


@pytest.mark.parametrize("machine_class", CLASSES)
def test_golden_rows_reproduce_from_artifact(machine_class):
    art = _artifact(MODELS_DIR, machine_class)
    golden = json.loads((PARITY_DIR / f"estimator.{machine_class}.golden.json").read_text(encoding="utf-8"))
    assert golden["artifact_id"] == art["artifact_id"] and len(golden["rows"]) == 50
    for row in golden["rows"]:
        inputs = dict(row["inputs"])
        baseline = inputs.pop("baseline_min")
        got = est.estimate_range(inputs, baseline, art)
        assert got["basis"] == row["basis"] == "comparable_history"
        for k in ("p10_min", "p50_min", "p90_min"):
            assert abs(got[k] - row[k]) <= golden["tolerance_min"]
        assert row["p10_min"] <= row["p50_min"] <= row["p90_min"]
