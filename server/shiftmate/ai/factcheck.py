"""Fact check for model output (technical spec §6.6 "Fact check"). Any failure → the caller falls back to its template.

1. Every number in output text (regex `\\d+(?:[.,]\\d+)?`) must equal, rounded to 1 dp, a number present in the facts,
   or a minutes↔hours conversion of a numeric fact whose key names minutes or hours.
2. Machine IDs (`[A-Z]{2}-\\d{2}`), zone names and operator names in the output must appear in the facts.
3. Negation (extraction): rules `no_incident` ⇒ model `no_incident`; rules `contact: no` ⇒ model never `yes`.
4. Extraction enums are valid (enforced by the Pydantic output model before this runs).
5. Handover text contains the item's key noun from its facts.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from typing import Any

NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
MACHINE_ID = re.compile(r"[A-Z]{2}-\d{2}")
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?Z?)?$")
KEY_NOUN_FIELDS = ("key_noun", "task_type_label", "defect_keyword")


def _canonical(facts: dict[str, Any]) -> str:
    return json.dumps(facts, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _numbers_in(text: str) -> set[float]:
    return {round(float(m.replace(",", ".")), 1) for m in NUMBER.findall(text)}


def _walk(value: Any, key: str = ""):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _walk(v, k)
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v, key)
    else:
        yield key, value


def allowed_numbers(facts: dict[str, Any]) -> set[float]:
    """Numeric fact values (+ minute/hour conversions) and numbers inside text facts such as "EX-07" or "m3".
    Timestamp strings are skipped: their digits are not quantities the model may quote."""
    allowed: set[float] = set()
    for key, value in _walk(facts):
        if isinstance(value, str) and not TIMESTAMP.match(value):
            allowed |= _numbers_in(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            allowed.add(round(float(value), 1))
            k = key.lower()
            if "min" in k:
                allowed.add(round(value / 60, 1))
            if "hour" in k or k.endswith("_h"):
                allowed.add(round(value * 60, 1))
    return allowed


def check_text(
    text: str, facts: dict[str, Any], *, zone_names: Iterable[str] = (), operator_names: Iterable[str] = ()
) -> list[str]:
    """Rules 1–2 for one piece of output text. Returns the problems found (empty = passes)."""
    problems = []
    canonical = _canonical(facts)
    invented = sorted(_numbers_in(text) - allowed_numbers(facts))
    if invented:
        problems.append(f"numbers not in facts: {invented}")
    for machine_id in set(MACHINE_ID.findall(text)):
        if machine_id not in canonical:
            problems.append(f"machine id not in facts: {machine_id}")
    for name in [*zone_names, *operator_names]:
        if name and name in text and name not in canonical:
            problems.append(f"name not in facts: {name}")
    return problems


def check_extraction(
    output: Any, rules_result: Any, facts: dict[str, Any], **names: Iterable[str]
) -> list[str]:
    problems = check_text(output.summary, facts, **names)
    if rules_result.no_incident and not output.no_incident:
        problems.append("rules say no incident; model says incident")
    if rules_result.contact == "no" and output.contact == "yes":
        problems.append("rules say no contact; model says contact")
    return problems


def key_noun(facts: dict[str, Any]) -> str | None:
    for field in KEY_NOUN_FIELDS:
        if isinstance(facts.get(field), str) and facts[field].strip():
            return facts[field].strip()
    return None


def check_handover_item(text: str, facts: dict[str, Any], **names: Iterable[str]) -> list[str]:
    problems = check_text(text, facts, **names)
    noun = key_noun(facts)
    if noun and noun.lower() not in text.lower():
        problems.append(f"key noun missing: {noun}")
    return problems
