import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from shiftmate_ml.paths import DEMO_HISTORY_PATH


def export_demo_history(
    ledger_entries: list[dict[str, Any]],
    anchor_date_str: str,
    output_path: Path = DEMO_HISTORY_PATH,
    lookback_days: int = 14,
) -> int:
    """Exports the last 14 days of ledger entries for EX-07, HT-03 and their operators to demo_history.json.

    Includes day offsets so that dates can be mapped relative to demo first-launch date.
    """
    anchor_dt = datetime.strptime(anchor_date_str, "%Y-%m-%d").replace(tzinfo=UTC)
    target_machines = {"EX-07", "HT-03"}

    demo_entries = []
    for entry in ledger_entries:
        if entry.get("machine_id") not in target_machines:
            continue

        obs_str = entry.get("observed_at") or entry.get("recorded_at")
        if not obs_str:
            continue

        # Parse timestamp: e.g. "2026-09-20T10:00:00.000Z"
        obs_dt = datetime.fromisoformat(obs_str)
        delta_days = (obs_dt.date() - anchor_dt.date()).days

        # We keep entries from [anchor_date - lookback_days, anchor_date]
        if -lookback_days <= delta_days <= 0:
            entry_copy = dict(entry)
            entry_copy["day_offset"] = delta_days
            demo_entries.append(entry_copy)

    # Sort ascending by observed_at then entry_id
    demo_entries.sort(key=lambda e: (e.get("observed_at", ""), e.get("entry_id", "")))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(demo_entries, f, indent=2)

    return len(demo_entries)
