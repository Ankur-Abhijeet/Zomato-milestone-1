"""Groq chat-completions client with retries and JSON mode."""

from __future__ import annotations

import logging
import time
from typing import Optional

from groq import Groq

from config.settings import Settings, get_settings
from models.integration import PromptPayload
from services.llm.exceptions import (
    LLMConfigError,
    LLMError,
    LLMQuotaError,
    LLMRateLimitError,
    LLMTimeoutError,
)

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


class GroqLLMClient:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()

    def complete(self, payload: PromptPayload) -> str:
        api_key = self._settings.groq_api_key
        if not api_key:
            raise LLMConfigError(
                "GROQ_API_KEY is not set. Add it to your .env file "
                "(see .env.example)."
            )

        client = Groq(api_key=api_key)
        last_error: Optional[Exception] = None

        for attempt in range(1, self._settings.llm_max_retries + 1):
            try:
                logger.info(
                    "Calling Groq model=%s (attempt %d/%d)",
                    self._settings.groq_model,
                    attempt,
                    self._settings.llm_max_retries,
                )
                response = client.chat.completions.create(
                    model=self._settings.groq_model,
                    messages=[
                        {"role": "system", "content": payload.system_message},
                        {"role": "user", "content": payload.user_message},
                    ],
                    response_format={"type": "json_object"},
                    temperature=self._settings.groq_temperature,
                    max_tokens=self._settings.groq_max_tokens,
                    timeout=self._settings.llm_timeout_seconds,
                )
                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise LLMError("Groq returned an empty response")
                if self._settings.log_llm_responses:
                    logger.debug("Groq raw response:\n%s", content)
                return content.strip()
            except Exception as exc:
                last_error = exc
                category = _classify_error(exc)
                logger.warning("Groq call failed (%s): %s", category, exc)

                if category == "quota":
                    raise LLMQuotaError(
                        "Groq API quota or billing limit reached. "
                        "Check your Groq account — recommendations were not generated."
                    ) from exc
                if category == "config":
                    raise LLMConfigError(str(exc)) from exc
                if category == "retryable" and attempt < self._settings.llm_max_retries:
                    sleep_for = self._settings.llm_retry_backoff_seconds * attempt
                    time.sleep(sleep_for)
                    continue
                if category == "timeout":
                    raise LLMTimeoutError(
                        f"Groq request timed out after {self._settings.llm_max_retries} attempts"
                    ) from exc
                if category == "rate_limit":
                    raise LLMRateLimitError(
                        f"Groq rate limit exceeded after {self._settings.llm_max_retries} attempts"
                    ) from exc
                raise LLMError(f"Groq API error: {exc}") from exc

        raise LLMError(f"Groq call failed: {last_error}") from last_error


def _classify_error(exc: Exception) -> str:
    status_code = getattr(exc, "status_code", None)
    if status_code is None:
        response = getattr(exc, "response", None)
        if response is not None:
            status_code = getattr(response, "status_code", None)

    if status_code in (401, 403):
        return "config"
    if status_code == 402:
        return "quota"

    name = type(exc).__name__.lower()
    message = str(exc).lower()
    if "rate" in name or "rate" in message or status_code == 429:
        return "rate_limit"
    if "timeout" in name or "timeout" in message or status_code == 408:
        return "timeout"
    if status_code in _RETRYABLE_STATUS:
        return "retryable"
    return "fatal"
