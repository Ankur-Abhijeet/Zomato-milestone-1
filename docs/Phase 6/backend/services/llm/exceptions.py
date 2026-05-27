"""LLM client errors (Phase 4)."""

from __future__ import annotations


class LLMError(RuntimeError):
    """Base error for LLM call failures (may trigger fallback)."""


class LLMConfigError(LLMError):
    """Missing or invalid configuration (fail fast, no fallback)."""


class LLMQuotaError(LLMError):
    """Billing / quota exhausted (fail fast, no fake AI explanations)."""


class LLMRateLimitError(LLMError):
    """Rate limited after retries (may trigger fallback)."""


class LLMTimeoutError(LLMError):
    """Request timed out after retries (may trigger fallback)."""
