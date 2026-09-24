"""DeepSeek client wrapper (technical spec §6.5, §6.6; T40 / S1 — provider changed from Anthropic to DeepSeek).

One `POST {DEEPSEEK_BASE_URL}/chat/completions` per use, in JSON mode (`response_format: json_object`) with thinking
disabled (it is on by default and would not fit the device timeout). The system prompt is the static template plus
the output model's JSON Schema; the user message is `<facts>` (canonical JSON) plus, when present, `<operator_text>`
(the only untrusted input). The reply is parsed into the Pydantic output model. Every failure maps to an
`unavailable` reason and the caller keeps its template: disabled/no key → `ai_disabled`, timeout → `timeout`,
HTTP 4xx/5xx or connection errors → `provider_error` (logged with the status, never the prompt),
`finish_reason == "content_filter"` → `refused`, truncated, empty or non-conforming output → `invalid_output`.

Tests inject an `httpx.Client` with a MockTransport as `app.state.ai_client`; production creates a plain client
lazily when AI_ENABLED and DEEPSEEK_API_KEY are set.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from shiftmate.ai.templates import Prompt
from shiftmate.config import settings

log = logging.getLogger("shiftmate.ai")

MAX_OPERATOR_TEXT = 500
MAX_FACTS_BYTES = 4096
RETRYABLE_STATUS = {429, 500, 503}  # DeepSeek: rate limited, server error, overloaded


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


def system_prompt(prompt: Prompt, output_model: type[BaseModel]) -> str:
    """Template + the exact output schema (JSON mode needs the word "json" and the expected format in the prompt)."""
    schema = json.dumps(output_model.model_json_schema(), ensure_ascii=False, separators=(",", ":"))
    return f"{prompt.system}\n\nReply with only a json object that conforms to this JSON Schema:\n{schema}"


class AIClient:
    def __init__(self, http: httpx.Client) -> None:
        self.http = http

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
        body = {
            "model": settings.AI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt(prompt, output_model)},
                {"role": "user", "content": content},
            ],
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "thinking": {"type": "disabled"},
            "stream": False,
        }
        url = settings.DEEPSEEK_BASE_URL.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY or ''}"}

        response: httpx.Response | None = None
        reason = "provider_error"
        for attempt in range(max_retries + 1):
            try:
                response = self.http.post(url, json=body, headers=headers, timeout=timeout)
            except httpx.TimeoutException:
                response, reason = None, "timeout"
                continue
            except httpx.HTTPError as exc:
                log.warning("ai_provider_error prompt=%s error=%s", prompt.version, type(exc).__name__)
                response, reason = None, "provider_error"
                continue
            if response.status_code in RETRYABLE_STATUS and attempt < max_retries:
                continue
            break
        if response is None:
            return AIResult(reason=reason, details=details)
        if response.status_code >= 400:
            hint = {401: "authentication failed - check DEEPSEEK_API_KEY", 402: "account out of balance"}
            log.warning(
                "ai_provider_error prompt=%s status=%s %s",
                prompt.version,
                response.status_code,
                hint.get(response.status_code, ""),
            )
            return AIResult(reason="provider_error", details=details)

        try:
            choice = response.json()["choices"][0]
            finish = choice.get("finish_reason")
            text = (choice.get("message") or {}).get("content") or ""
        except (ValueError, KeyError, IndexError, TypeError):
            return AIResult(reason="invalid_output", details=details)
        if finish == "content_filter":
            return AIResult(reason="refused", details=details)
        if finish == "insufficient_system_resource":
            return AIResult(reason="provider_error", details=details)
        if finish == "length" or not text.strip():  # truncated JSON, or DeepSeek's occasional empty content
            return AIResult(reason="invalid_output", details=details)
        try:
            parsed = output_model.model_validate(json.loads(text))
        except (ValueError, ValidationError):
            return AIResult(reason="invalid_output", details=details)
        return AIResult(parsed=parsed, details=details)


def get_ai_client(state: Any) -> AIClient | None:
    """The AI client for this app (`app.state`), or None when AI is disabled or has no credentials."""
    if not settings.AI_ENABLED:
        return None
    http = getattr(state, "ai_client", None)
    if http is None:
        if not settings.DEEPSEEK_API_KEY:
            return None
        http = httpx.Client()
        state.ai_client = http
    return AIClient(http)
