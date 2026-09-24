"""Ridge task-time estimator training (technical spec §8.6.2–§8.6.4, §8.22; task T36).

The encoding here is the device's §8.6.2 encoding: one column per non-reference categorical level, numeric
features clipped, transformed and standardised with training statistics. The artifact stores exactly the
fitted coefficients, so `predict_log_ratio` reproduces the device prediction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV

ALPHAS = [0.1, 0.3, 1, 3, 10, 30]
MIN_TASK_TYPE_COUNT = 30
MIN_CALIBRATION_N = 30
FALLBACK_BAND = {"lo": 0.8, "hi": 1.35}
DECIMALS = 6

# Profile task-type order per class; the first is the reference level.
TASK_TYPES = {
    "excavator": ["trenching", "truck_loading", "backfilling", "grading", "pipe_lifting"],
    "haul_truck": ["haul_overburden", "haul_ore"],
}
# Canonical material order; "any" (count tasks) is left out because task_type already carries it.
MATERIAL_ORDER = ["clay", "sand", "gravel", "topsoil", "rock", "overburden", "ore"]

# (name, group, tasks.csv column, levels, reference). task_type/material levels are filled per class.
CATEGORICAL_BASE = [
    ("skill_level", "skill", "skill_level_at_start", ["beginner", "intermediate", "expert"], "intermediate"),
    ("task_type", "task_type", "task_type", None, None),
    ("material", "material", "material", None, None),
    ("weather", "weather", "weather_at_start", ["clear", "rain", "windy", "dusty", "foggy"], "clear"),
    ("visibility", "visibility", "visibility_at_start", ["good", "moderate", "poor"], "good"),
    (
        "temperature_band",
        "temperature",
        "temperature_band_at_start",
        ["cool", "mild", "hot", "extreme"],
        "mild",
    ),
    (
        "time_of_day",
        "time_of_day",
        "time_of_day_at_start",
        ["morning", "afternoon", "evening", "night"],
        "morning",
    ),
    ("site_congestion", "congestion", "site_congestion_at_start", ["low", "medium", "high"], "low"),
]
# (name, group, source feature, tasks.csv column, transform, clip)
NUMERIC_BASE = [
    ("experience", "experience", "experience_months", "experience_months_at_start", "log1p", [0, 240]),
    ("machine_age", "machine_age", "machine_age_years", "machine_age_years_at_start", "identity", [0, 25]),
]
# Raw feature names as the device sees them (§8.6.2) → tasks.csv column
FEATURE_COLUMNS = {c[0]: c[2] for c in CATEGORICAL_BASE} | {n[2]: n[3] for n in NUMERIC_BASE}

_TRANSFORMS = {"log1p": math.log1p, "ln": math.log, "identity": lambda v: v}


@dataclass
class FitResult:
    artifact_fields: dict[str, Any]
    fit_rows: pd.DataFrame
    calibration_rows: pd.DataFrame
    test_rows: pd.DataFrame


def raw_features(row: dict[str, Any] | pd.Series) -> dict[str, Any]:
    """Device-shaped raw inputs (§8.6.2 names) from one tasks.csv row."""
    return {name: _clean(row[col]) for name, col in FEATURE_COLUMNS.items()}


def _clean(v: Any) -> Any:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def build_spec(machine_class: str, rows: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    materials = [m for m in MATERIAL_ORDER if m in set(rows["material"])]
    categorical = []
    for name, group, _col, levels, ref in CATEGORICAL_BASE:
        if name == "task_type":
            levels, ref = TASK_TYPES[machine_class], TASK_TYPES[machine_class][0]
        elif name == "material":
            levels, ref = materials, materials[0]
        categorical.append({"name": name, "group": group, "levels": list(levels), "reference": ref})
    numeric = []
    for name, group, source, col, transform, clip in NUMERIC_BASE:
        v = rows[col].astype(float).clip(clip[0], clip[1]).map(_TRANSFORMS[transform])
        std = float(v.std(ddof=0)) or 1.0
        numeric.append(
            {
                "name": name,
                "group": group,
                "source": source,
                "transform": transform,
                "clip": clip,
                "mean": round(float(v.mean()), DECIMALS),
                "std": round(std, DECIMALS),
            }
        )
    return categorical, numeric


def column_keys(categorical: list[dict], numeric: list[dict]) -> list[str]:
    keys = [f"{c['name']}={lvl}" for c in categorical for lvl in c["levels"] if lvl != c["reference"]]
    return keys + [n["name"] for n in numeric]


def encode(features: dict[str, Any], categorical: list[dict], numeric: list[dict]) -> dict[str, float]:
    """§8.6.2 vector for one set of raw inputs. Unknown categorical levels encode as all zeros."""
    x: dict[str, float] = {}
    for c in categorical:
        v = features.get(c["name"])
        for lvl in c["levels"]:
            if lvl != c["reference"]:
                x[f"{c['name']}={lvl}"] = 1.0 if v == lvl else 0.0
    for n in numeric:
        lo, hi = n["clip"]
        v = min(max(float(features[n["source"]]), lo), hi)
        x[n["name"]] = (_TRANSFORMS[n["transform"]](v) - n["mean"]) / n["std"]
    return x


def encode_frame(rows: pd.DataFrame, categorical: list[dict], numeric: list[dict]) -> np.ndarray:
    keys = column_keys(categorical, numeric)
    return np.array(
        [[encode(raw_features(r), categorical, numeric)[k] for k in keys] for _, r in rows.iterrows()],
        dtype=float,
    )


def predict_log_ratio(features: dict[str, Any], art: dict[str, Any]) -> float:
    x = encode(features, art["categorical"], art["numeric"])
    return art["intercept"] + sum(art["coefficients"].get(k, 0.0) * v for k, v in x.items())


def conformal_quantiles(residuals: np.ndarray) -> dict[str, Any]:
    """§8.6.4 split-conformal quantiles: k_lo = max(1, ⌊0.1(n+1)⌋), k_hi = min(n, ⌈0.9(n+1)⌉) (1-based)."""
    r = np.sort(np.asarray(residuals, dtype=float))
    n = len(r)
    k_lo = max(1, math.floor(0.1 * (n + 1)))
    k_hi = min(n, math.ceil(0.9 * (n + 1)))
    return {
        "n": n,
        "q_lo": round(float(r[k_lo - 1]), DECIMALS),
        "q_mid": round(float(np.median(r)), DECIMALS),
        "q_hi": round(float(r[k_hi - 1]), DECIMALS),
    }


def estimate_range(
    features: dict[str, Any], baseline_min: float | None, art: dict[str, Any]
) -> dict[str, Any]:
    """§8.6.4 basis and P10/P50/P90 (no personal offset), mirroring the device's estimateService."""
    if baseline_min is None:
        return {"basis": "insufficient_data", "p10_min": None, "p50_min": None, "p90_min": None}
    tt = features["task_type"]
    tt_levels = next(c["levels"] for c in art["categorical"] if c["name"] == "task_type")
    band = art.get("fallback_band", FALLBACK_BAND)
    if tt not in tt_levels or art["task_type_counts"].get(tt, 0) < art["min_task_type_count"]:
        vals = [baseline_min * band["lo"], baseline_min, baseline_min * band["hi"]]
        basis = "fallback"
    else:
        by_tt = art["residual_quantiles"]["by_task_type"].get(tt)
        q = by_tt if by_tt and by_tt["n"] >= art["min_calibration_n"] else art["residual_quantiles"]["pooled"]
        eta = predict_log_ratio(features, art)
        vals = [baseline_min * math.exp(eta + q[k]) for k in ("q_lo", "q_mid", "q_hi")]
        basis = "comparable_history"
    p10, p50, p90 = sorted(vals)
    return {"basis": basis, "p10_min": round(p10, 1), "p50_min": round(p50, 1), "p90_min": round(p90, 1)}


def target(rows: pd.DataFrame) -> np.ndarray:
    return np.log(rows["actual_active_min"].astype(float) / rows["baseline_minutes"].astype(float)).to_numpy()


def load_class_rows(tasks: pd.DataFrame, machines: pd.DataFrame, machine_class: str) -> pd.DataFrame:
    """Training-eligible rows of one machine class, in file order."""
    cls = machines.set_index("machine_id")["machine_class"]
    rows = tasks[(tasks["machine_id"].map(cls) == machine_class) & _truthy(tasks["training_eligible"])]
    return rows.reset_index(drop=True)


def _truthy(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().isin(["true", "1"])


def fit(rows: pd.DataFrame, machine_class: str, split_col: str) -> FitResult:
    """Fit on split `train`, calibrate on `calibration`; `test` rows are returned untouched."""
    fit_rows = rows[rows[split_col] == "train"].reset_index(drop=True)
    cal_rows = rows[rows[split_col] == "calibration"].reset_index(drop=True)
    test_rows = rows[rows[split_col] == "test"].reset_index(drop=True)

    categorical, numeric = build_spec(machine_class, fit_rows)
    keys = column_keys(categorical, numeric)
    model = RidgeCV(alphas=ALPHAS, cv=5).fit(encode_frame(fit_rows, categorical, numeric), target(fit_rows))

    fields: dict[str, Any] = {
        "alpha": float(model.alpha_),
        "categorical": categorical,
        "numeric": numeric,
        "coefficients": {k: round(float(c), DECIMALS) for k, c in zip(keys, model.coef_)},
        "intercept": round(float(model.intercept_), DECIMALS),
        "task_type_counts": {
            tt: int((fit_rows["task_type"] == tt).sum()) for tt in TASK_TYPES[machine_class]
        },
        "min_task_type_count": MIN_TASK_TYPE_COUNT,
        "min_calibration_n": MIN_CALIBRATION_N,
        "fallback_band": dict(FALLBACK_BAND),
    }
    # Residuals use the rounded coefficients so the quantiles match what the device computes.
    resid = target(cal_rows) - np.array(
        [predict_log_ratio(raw_features(r), fields) for _, r in cal_rows.iterrows()]
    )
    fields["residual_quantiles"] = {
        "pooled": conformal_quantiles(resid),
        "by_task_type": {
            tt: conformal_quantiles(resid[(cal_rows["task_type"] == tt).to_numpy()])
            for tt in TASK_TYPES[machine_class]
            if (cal_rows["task_type"] == tt).any()
        },
    }
    return FitResult(fields, fit_rows, cal_rows, test_rows)


def predict_rows(rows: pd.DataFrame, art: dict[str, Any]) -> pd.DataFrame:
    out = [estimate_range(raw_features(r), float(r["baseline_minutes"]), art) for _, r in rows.iterrows()]
    return pd.DataFrame(out, index=rows.index)


def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(predicted - actual) / actual))


if __name__ == "__main__":  # `pnpm ml:train` entry point (§10.6)
    from shiftmate_ml.train.export import main

    main()
