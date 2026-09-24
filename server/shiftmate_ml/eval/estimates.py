"""Estimate evaluation (technical spec §8.22 "Estimate evaluation"; B1/T36).

For each split (A temporal, B unseen operators), machine class and task type, on identical test rows:
MAE (min), MAPE, P10–P90 coverage, mean relative width (P90 − P10)/P50 and bias (mean signed error) for
(1) task-type average, (2) baseline formula, (3) planner, (4) Ridge + conformal. The same is repeated on the
`sens_0.5` / `sens_1.5` bundles. Writes `eval/results/estimates.json`.

Usage: `uv run python -m shiftmate_ml.eval.estimates`
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from shiftmate_ml.paths import EVAL_RESULTS_DIR, GENERATED_DIR
from shiftmate_ml.train import estimator as est
from shiftmate_ml.train.export import CLASSES, load_bundle

SPLITS = {"A": "split_temporal", "B": "split_unseen_operator"}
SENSITIVITIES = ["sens_0.5", "sens_1.5"]


def metrics(
    actual: np.ndarray, p50: np.ndarray, p10: np.ndarray | None, p90: np.ndarray | None
) -> dict[str, Any]:
    err = p50 - actual
    out: dict[str, Any] = {
        "n": len(actual),
        "mae_min": round(float(np.mean(np.abs(err))), 3),
        "mape": round(float(np.mean(np.abs(err) / actual)), 4),
        "bias_min": round(float(np.mean(err)), 3),
        "p10_p90_coverage": None,
        "mean_relative_width": None,
    }
    if p10 is not None and p90 is not None:
        out["p10_p90_coverage"] = round(float(np.mean((actual >= p10) & (actual <= p90))), 4)
        out["mean_relative_width"] = round(float(np.mean((p90 - p10) / p50)), 4)
    return out


def method_predictions(result: est.FitResult, art: dict[str, Any]) -> dict[str, tuple]:
    test, fit_rows = result.test_rows, result.fit_rows
    baseline = test["baseline_minutes"].to_numpy(float)
    # (1) Task-type average: median active minutes per unit in training × quantity
    per_unit = (fit_rows["actual_active_min"] / fit_rows["quantity"]).groupby(fit_rows["task_type"]).median()
    tt_avg = (test["task_type"].map(per_unit) * test["quantity"]).to_numpy(float)
    ridge = est.predict_rows(test, art)
    band = art["fallback_band"]
    return {
        "task_type_average": (tt_avg, None, None),
        "baseline": (baseline, baseline * band["lo"], baseline * band["hi"]),
        "planner": (test["planner_minutes"].to_numpy(float), None, None),
        "ridge_conformal": tuple(ridge[k].to_numpy(float) for k in ("p50_min", "p10_min", "p90_min")),
    }


def evaluate_split(rows: pd.DataFrame, machine_class: str, split_col: str) -> dict[str, Any]:
    result = est.fit(rows, machine_class, split_col)
    art = {"artifact_id": f"eval.{machine_class}", **result.artifact_fields}
    preds = method_predictions(result, art)
    test = result.test_rows
    actual = test["actual_active_min"].to_numpy(float)
    groups = {"all": np.ones(len(test), dtype=bool)}
    groups |= {
        tt: (test["task_type"] == tt).to_numpy()
        for tt in est.TASK_TYPES[machine_class]
        if (test["task_type"] == tt).any()
    }
    out: dict[str, Any] = {
        "alpha": art["alpha"],
        "n_fit": len(result.fit_rows),
        "n_calibration": len(result.calibration_rows),
        "by_task_type": {},
    }
    for name, mask in groups.items():
        out["by_task_type"][name] = {
            method: metrics(
                actual[mask],
                p50[mask],
                None if p10 is None else p10[mask],
                None if p90 is None else p90[mask],
            )
            for method, (p50, p10, p90) in preds.items()
        }
    return out


def evaluate_bundle(data_dir: Path) -> dict[str, Any]:
    tasks, machines, manifest = load_bundle(data_dir)
    out: dict[str, Any] = {"data_origin": manifest["data_origin"], "classes": {}}
    for machine_class in CLASSES:
        rows = est.load_class_rows(tasks, machines, machine_class)
        out["classes"][machine_class] = {
            f"split_{k}": evaluate_split(rows, machine_class, col) for k, col in SPLITS.items()
        }
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Evaluate task-time estimates")
    ap.add_argument("--data-dir", type=Path, default=GENERATED_DIR)
    ap.add_argument("--out", type=Path, default=EVAL_RESULTS_DIR / "estimates.json")
    args = ap.parse_args(argv)

    results: dict[str, Any] = {
        "banner": "SIMULATED DATA",
        "methods": ["task_type_average", "baseline", "planner", "ridge_conformal"],
        "not_run": {
            "lightgbm_shap": "not run: S7 comparison (lightgbm/shap ml extras) is not part of B1",
            "organiser": "not run: no organiser task rows mapped (E-01)",
        },
        "main": evaluate_bundle(args.data_dir),
        "sensitivity": {},
    }
    for sens in SENSITIVITIES:
        sens_dir = args.data_dir / sens
        results["sensitivity"][sens] = (
            evaluate_bundle(sens_dir)
            if (sens_dir / "tasks.csv").exists()
            else f"not run: {sens_dir} missing (run datagen --all-sensitivities)"
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")

    for bundle, res in [("main", results["main"])] + [
        (k, v) for k, v in results["sensitivity"].items() if isinstance(v, dict)
    ]:
        for machine_class, splits in res["classes"].items():
            for split, r in splits.items():
                a = r["by_task_type"]["all"]
                print(
                    f"{bundle:9} {machine_class:10} {split}: "
                    + " | ".join(f"{m} mae={v['mae_min']} cov={v['p10_p90_coverage']}" for m, v in a.items())
                )
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
