from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from shiftmate_ml.paths import CONFIG_PATH


@dataclass
class GenConfig:
    schema_version: str
    generator_version: str
    seed: int
    anchor_date: str
    data_origin: str
    num_weeks: int
    working_days_per_week: int
    split_policy: dict[str, Any]
    effects: dict[str, Any]
    planner: dict[str, Any]
    waits: dict[str, Any]
    sensitivity: dict[str, Any]
    raw: dict[str, Any] = field(default_factory=dict)


def load_config(config_path: Path | None = None) -> GenConfig:
    path = config_path or CONFIG_PATH
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return GenConfig(
        schema_version=data.get("schema_version", "1.2.0"),
        generator_version=data.get("generator_version", "gen-1.0"),
        seed=data.get("seed", 20260923),
        anchor_date=data.get("anchor_date", "2026-09-22"),
        data_origin=data.get("data_origin", f"synthetic:gen-1.0:{data.get('seed', 20260923)}"),
        num_weeks=data.get("num_weeks", 12),
        working_days_per_week=data.get("working_days_per_week", 6),
        split_policy=data.get("split_policy", {}),
        effects=data.get("effects", {}),
        planner=data.get("planner", {}),
        waits=data.get("waits", {}),
        sensitivity=data.get("sensitivity", {}),
        raw=data,
    )
