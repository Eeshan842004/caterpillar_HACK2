"""Prompt templates (`ai/prompts/*.md`, first line `version: <name>@<n>`), loaded once at import (§6.6)."""

from dataclasses import dataclass
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    system: str


def _load(name: str) -> Prompt:
    header, _, body = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").partition("\n")
    if not header.startswith("version: "):
        raise ValueError(f"prompt {name} has no version header")
    return Prompt(name=name, version=header.removeprefix("version: ").strip(), system=body.strip())


PROMPTS = {n: _load(n) for n in ("incident_extract", "handover_wording", "ask", "scenario_draft")}
