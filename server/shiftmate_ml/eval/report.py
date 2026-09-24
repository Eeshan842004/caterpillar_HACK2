"""Evaluation report (product §17.2, technical spec M19-R1, T39 Python part): `eval/results/results.json` + `results.md`.

Carries the "SIMULATED DATA" banner, the generator seed and the git commit. Every §17.2 section is present: filled
from the results that exist (estimates today) or marked "not run: <reason>". Opened on the laptop at demo beat 4:45.

Usage: `uv run python -m shiftmate_ml.eval.report [--run-estimates]`
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shiftmate_ml.paths import EVAL_RESULTS_DIR, GENERATED_DIR, ROOT_DIR

METHOD_LABELS = {
    "task_type_average": "Task-type average",
    "baseline": "Baseline formula",
    "planner": "Planner estimate",
    "ridge_conformal": "ShiftMate (Ridge + conformal)",
}
SPLIT_LABELS = {"split_A": "Split A — later weeks (weeks 11–12)", "split_B": "Split B — unseen operators"}

# §17.2 sections that have no evaluation input in this build yet, with the reason shown in the report.
NOT_RUN = {
    "safety": (
        "Safety behaves?",
        "not run: safety challenge scenarios run in the behaviour eval (tools/eval, T39), not built yet",
    ),
    "alert_budget": (
        "Alert budget respected?",
        "not run: needs the behaviour eval scenarios (tools/eval, T39)",
    ),
    "usage_review": ("Usage review fair?", "not run: needs the paired usage scenarios (tools/eval, T39)"),
    "training": ("Training relevant?", "not run: needs the recommendation scenarios (tools/eval, T39)"),
    "voice": (
        "Voice works?",
        "not run: intent model and held-out voice set (T37, data/voice_test) not available",
    ),
    "propagation": ("Propagation consistent?", "not run: needs the propagation scenarios (tools/eval, T39)"),
    "organiser": ("Organiser compatibility", "not run: organiser data mapping (E-01, T38) not available"),
    "operator_effort": ("Operator effort", "not run: needs the scripted journeys (tools/eval, T39)"),
}


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return out.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _pct(v: float | None) -> str:
    return "—" if v is None else f"{v * 100:.0f}%"


def _num(v: float | None) -> str:
    return "—" if v is None else f"{v:.1f}"


def estimate_summary(estimates: dict[str, Any]) -> dict[str, Any]:
    """All-task-type metrics per class, split and method (main bundle) + ShiftMate coverage on the sensitivities."""
    out: dict[str, Any] = {"main": {}, "sensitivity": {}}
    for cls, splits in estimates["main"]["classes"].items():
        out["main"][cls] = {split: r["by_task_type"]["all"] for split, r in splits.items()}
    for name, res in estimates.get("sensitivity", {}).items():
        if isinstance(res, dict):
            out["sensitivity"][name] = {
                cls: {split: r["by_task_type"]["all"]["ridge_conformal"] for split, r in splits.items()}
                for cls, splits in res["classes"].items()
            }
        else:
            out["sensitivity"][name] = res
    return out


def render_markdown(meta: dict[str, Any], summary: dict[str, Any] | None, estimates_note: str | None) -> str:
    lines = [
        "# ShiftMate evaluation results",
        "",
        (
            "> **SIMULATED DATA** — every number below comes from the synthetic dataset "
            f"(`{meta['data_origin']}`), not from real machines or operators. Thresholds are illustrative."
        ),
        "",
        (
            f"Generator `{meta['generator_version']}` · seed `{meta['seed']}` · commit `{meta['git_commit']}` · "
            f"generated {meta['generated_at']}"
        ),
        "",
        "## Estimates useful?",
        "",
    ]
    if summary is None:
        lines += [estimates_note or "not run", ""]
    else:
        lines += [
            "Active minutes per task on held-out rows. Lower MAE is better; P10–P90 coverage should be near 80%.",
            "",
        ]
        for cls, splits in summary["main"].items():
            for split, methods in splits.items():
                lines += [
                    f"### {cls.replace('_', ' ').title()} — {SPLIT_LABELS.get(split, split)}",
                    "",
                    "| Method | MAE (min) | MAPE | Bias (min) | P10–P90 coverage | Relative width |",
                    "|---|---|---|---|---|---|",
                ]
                for method, m in methods.items():
                    lines.append(
                        f"| {METHOD_LABELS.get(method, method)} | {_num(m['mae_min'])} | {_pct(m['mape'])} "
                        f"| {_num(m['bias_min'])} | {_pct(m['p10_p90_coverage'])} "
                        f"| {_num(m['mean_relative_width'])} |"
                    )
                lines.append("")
        lines += [
            "### Sensitivity (effects × 0.5 / × 1.5) — ShiftMate coverage and MAE",
            "",
            "| Bundle | Class | Split | MAE (min) | P10–P90 coverage |",
            "|---|---|---|---|---|",
        ]
        for name, res in summary["sensitivity"].items():
            if isinstance(res, str):
                lines.append(f"| {name} | — | — | {res} | — |")
                continue
            for cls, splits in res.items():
                for split, m in splits.items():
                    lines.append(
                        f"| {name} | {cls} | {split} | {_num(m['mae_min'])} | {_pct(m['p10_p90_coverage'])} |"
                    )
        lines.append("")
    for title, reason in NOT_RUN.values():
        lines += [f"## {title}", "", reason, ""]
    lines += [
        "## Not claimed",
        "",
        "Field accuracy, accident reduction, fuel savings, lasting learning improvement, certified safety distances.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Write eval/results/results.json and results.md")
    ap.add_argument("--run-estimates", action="store_true", help="Re-run the estimate evaluation first")
    ap.add_argument("--out-dir", type=Path, default=EVAL_RESULTS_DIR)
    ap.add_argument("--data-dir", type=Path, default=GENERATED_DIR)
    args = ap.parse_args(argv)

    estimates_path = args.out_dir / "estimates.json"
    if args.run_estimates:
        from shiftmate_ml.eval import estimates

        estimates.main(["--data-dir", str(args.data_dir), "--out", str(estimates_path)])

    manifest_path = args.data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    meta = {
        "banner": "SIMULATED DATA",
        "generator_version": manifest.get("generator_version", "unknown"),
        "seed": manifest.get("seed", "unknown"),
        "data_origin": manifest.get("data_origin", "unknown"),
        "git_commit": _git_commit(),
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    summary, note = None, None
    if estimates_path.exists():
        summary = estimate_summary(json.loads(estimates_path.read_text(encoding="utf-8")))
    else:
        note = "not run: eval/results/estimates.json missing (run with --run-estimates)"

    results = {
        **meta,
        "sections": {
            "estimates": summary if summary is not None else note,
            **{key: reason for key, (_, reason) in NOT_RUN.items()},
        },
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    (args.out_dir / "results.md").write_text(
        render_markdown(meta, summary, note), encoding="utf-8", newline="\n"
    )
    print(f"wrote {args.out_dir / 'results.md'} and results.json")


if __name__ == "__main__":
    main()
