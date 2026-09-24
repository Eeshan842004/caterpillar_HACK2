"""Anthropic client wrapper (technical spec §6.5, §6.6; T40 / S1).

`messages.parse` with a Pydantic output model; per-call timeout/retries via `with_options`. The system prompt is the
static template; the user message is `<facts>` (canonical JSON) plus, when present, `<operator_text>` (the only
untrusted input). Every failure maps to an `unavailable` reason and the caller keeps its template:
disabled/no key → `ai_disabled`, `APITimeoutError` → `timeout`, rate-limit/status/connection errors →
`provider_error` (logged with the request id, never the prompt), `stop_reason == "refusal"` → `refused`,
truncated or unparsable output → `invalid_output`.

Tests inject a fake raw client as `app.state.ai_client`; production creates the real one lazily when AI_ENABLED and
ANTHROPIC_API_KEY are set.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import anthropic
from pydantic import BaseModel

from shiftmate.ai.templates import Prompt
from shiftmate.config import settings

log = logging.getLogger("shiftmate.ai")

MAX_OPERATOR_TEXT = 500
MAX_FACTS_BYTES = 4096


@dataclass
class AIResult:
    parsed: Any = None
    reason: str | None = None  # set when unavailable
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.reason is None


def canonical_facts(facts: dict[str, Any]) -> str:
    return json.dumps(facts, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class AIClient:
    def __init__(self, raw: Any) -> None:
        self.raw = raw

    def call(
        self,
        prompt: Prompt,
        facts: dict[str, Any],
        output_model: type[BaseModel],
        *,
        max_tokens: int,
        timeout: float,
        max_retries: int = 0,
        operator_text: str | None = None,
    ) -> AIResult:
        details: dict[str, Any] = {}
        content = f"<facts>\n{canonical_facts(facts)}\n</facts>"
        if operator_text is not None:
            if len(operator_text) > MAX_OPERATOR_TEXT:
                operator_text = operator_text[:MAX_OPERATOR_TEXT]
                details["operator_text_truncated"] = True
            content += f"\n<operator_text>\n{operator_text}\n</operator_text>"
        try:
            response = self.raw.with_options(timeout=timeout, max_retries=max_retries).messages.parse(
                model=settings.AI_MODEL,
                max_tokens=max_tokens,
                system=prompt.system,
                messages=[{"role": "user", "content": content}],
                output_format=output_model,
            )
        except anthropic.APITimeoutError:
            return AIResult(reason="timeout", details=details)
        except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
            log.warning(
                "ai_provider_error prompt=%s type=%s request_id=%s",
                prompt.version,
                type(exc).__name__,
                getattr(exc, "request_id", None),
            )
            return AIResult(reason="provider_error", details=details)
        except ValueError:  # malformed JSON / schema mismatch in the parsed output
            return AIResult(reason="invalid_output", details=details)
        if response.stop_reason == "refusal":
            return AIResult(reason="refused", details=details)
        if response.stop_reason == "max_tokens" or response.parsed_output is None:
            return AIResult(reason="invalid_output", details=details)
        return AIResult(parsed=response.parsed_output, details=details)


def get_ai_client(state: Any) -> AIClient | None:
    """The AI client for this app (`app.state`), or None when AI is disabled or has no credentials."""
    if not settings.AI_ENABLED:
        return None
    raw = getattr(state, "ai_client", None)
    if raw is None:
        if not settings.ANTHROPIC_API_KEY:
            return None
        raw = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, max_retries=0)
        state.ai_client = raw
    return AIClient(raw)
