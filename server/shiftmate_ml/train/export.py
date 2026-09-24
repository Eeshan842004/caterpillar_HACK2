"""Trains the per-class estimators and writes the bundled artifacts (§5.4.4) and golden parity files (T36).

Usage: `uv run python -m shiftmate_ml.train.export [--data-dir ../data/generated]`
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from shiftmate_ml.paths import GENERATED_DIR, MODELS_DIR, PARITY_DIR
from shiftmate_ml.train import estimator as est

CLASSES = ["excavator", "haul_truck"]
GOLDEN_ROWS = 50
VERSION = 1


def load_bundle(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    tasks = pd.read_csv(data_dir / "tasks.csv", keep_default_na=False, na_values=[""])
    machines = pd.read_csv(data_dir / "machines.csv", keep_default_na=False, na_values=[""])
    manifest = json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))
    return tasks, machines, manifest


def split_mape(result: est.FitResult, art: dict[str, Any]) -> float:
    rows = result.test_rows
    pred = est.predict_rows(rows, art)
    return round(est.mape(rows["actual_active_min"].to_numpy(float), pred["p50_min"].to_numpy(float)), 4)


def build_artifact(
    rows: pd.DataFrame, machine_class: str, manifest: dict[str, Any]
) -> tuple[dict, est.FitResult]:
    split_a = est.fit(rows, machine_class, "split_temporal")
    split_b = est.fit(rows, machine_class, "split_unseen_operator")
    art: dict[str, Any] = {
        "artifact_id": f"estimator.{machine_class}@{VERSION}",
        "kind": "estimator",
        "machine_class": machine_class,
        "version": VERSION,
        # Deterministic: the bundle's fixed generation time, not the wall clock.
        "trained_at": manifest["generated_at"],
        "data_origin": manifest["data_origin"],
        "target": "ln(actual_active_min / baseline_min)",
        **split_a.artifact_fields,
    }
    b_art = {**art, **split_b.artifact_fields}
    art["metrics"] = {
        "split_a_test_mape": split_mape(split_a, art),
        "split_b_test_mape": split_mape(split_b, b_art),
    }
    return art, split_a


def golden_rows(result: est.FitResult, art: dict[str, Any]) -> list[dict[str, Any]]:
    """50 split-A test rows spread across the test set (stable, evenly spaced picks)."""
    rows = result.test_rows
    idx = np.unique(np.linspace(0, len(rows) - 1, min(GOLDEN_ROWS, len(rows))).round().astype(int))
    out = []
    for i in idx:
        r = rows.iloc[int(i)]
        features = est.raw_features(r)
        baseline = float(r["baseline_minutes"])
        out.append(
            {
                "task_id": r["task_id"],
                "inputs": {**features, "baseline_min": baseline},
                "pred": round(est.predict_log_ratio(features, art), 6),
                **est.estimate_range(features, baseline, art),
            }
        )
    return out


def write_json(path: Path, body: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Train and export the estimator artifacts")
    ap.add_argument("--data-dir", type=Path, default=GENERATED_DIR)
    ap.add_argument("--models-dir", type=Path, default=MODELS_DIR)
    ap.add_argument("--parity-dir", type=Path, default=PARITY_DIR)
    args = ap.parse_args(argv)

    tasks, machines, manifest = load_bundle(args.data_dir)
    for machine_class in CLASSES:
        rows = est.load_class_rows(tasks, machines, machine_class)
        art, split_a = build_artifact(rows, machine_class, manifest)
        write_json(args.models_dir / f"estimator.{machine_class}.v{VERSION}.json", art)
        write_json(
            args.parity_dir / f"estimator.{machine_class}.golden.json",
            {
                "artifact_id": art["artifact_id"],
                "note": "Split-A test rows; p10/p50/p90 from the artifact with no personal offset (§8.6.4).",
                "tolerance_min": 0.1,
                "rows": golden_rows(split_a, art),
            },
        )
        print(
            f"{machine_class}: alpha={art['alpha']} n_fit={len(split_a.fit_rows)} "
            f"n_cal={len(split_a.calibration_rows)} metrics={art['metrics']}"
        )


if __name__ == "__main__":
    main()
