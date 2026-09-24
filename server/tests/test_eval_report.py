"""Evaluation report (§17.2, M19-R1): banner, seed, commit, filled estimate section, every other section marked."""

import json

from shiftmate_ml.eval import report

METRICS = {
    "n": 10,
    "mae_min": 7.8,
    "mape": 0.16,
    "bias_min": -1.4,
    "p10_p90_coverage": 0.8,
    "mean_relative_width": 0.6,
}


def test_report_has_banner_estimates_and_every_section(tmp_path):
    split = {
        "alpha": 3.0,
        "n_fit": 1,
        "n_calibration": 1,
        "by_task_type": {"all": {m: dict(METRICS) for m in report.METHOD_LABELS}},
    }
    estimates = {
        "main": {"classes": {"excavator": {"split_A": split, "split_B": split}}},
        "sensitivity": {
            "sens_0.5": {"classes": {"excavator": {"split_A": split}}},
            "sens_1.5": "not run: missing",
        },
    }
    (tmp_path / "estimates.json").write_text(json.dumps(estimates), encoding="utf-8")
    report.main(["--out-dir", str(tmp_path)])

    md = (tmp_path / "results.md").read_text(encoding="utf-8")
    assert "**SIMULATED DATA**" in md and "seed `20260923`" in md
    assert "| ShiftMate (Ridge + conformal) | 7.8 | 16% | -1.4 | 80% | 0.6 |" in md
    for title, reason in report.NOT_RUN.values():
        assert f"## {title}" in md and reason in md
    data = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert data["banner"] == "SIMULATED DATA" and set(report.NOT_RUN) <= set(data["sections"])
    assert data["sections"]["estimates"]["main"]["excavator"]["split_A"]["ridge_conformal"]["mae_min"] == 7.8


def test_missing_estimates_is_marked_not_run(tmp_path):
    report.main(["--out-dir", str(tmp_path)])
    assert "not run: eval/results/estimates.json missing" in (tmp_path / "results.md").read_text(
        encoding="utf-8"
    )
