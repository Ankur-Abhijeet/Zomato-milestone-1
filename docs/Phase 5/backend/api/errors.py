"""Global exception handlers (Phase 5a).

Maps domain errors to stable HTTP error shapes so the frontend
always receives a consistent `{"error": "<code>", "message": "..."}` body.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from input.validator import PreferenceValidationError
from services.llm.exceptions import LLMConfigError, LLMError, LLMQuotaError, LLMTimeoutError

logger = logging.getLogger(__name__)


def _error_body(code: str, message: str) -> dict:
    return {"error": code, "message": message}


def register_error_handlers(app: FastAPI) -> None:
    """Attach all domain → HTTP error handlers to the given FastAPI app."""

    @app.exception_handler(PreferenceValidationError)
    async def _handle_preference_validation(
        request: Request, exc: PreferenceValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Invalid preferences",
                "detail": exc.errors,
            },
        )

    @app.exception_handler(LLMQuotaError)
    async def _handle_quota(request: Request, exc: LLMQuotaError) -> JSONResponse:
        logger.error("Groq quota/billing error: %s", exc)
        return JSONResponse(
            status_code=502,
            content=_error_body(
                "llm_quota_exceeded",
                "The AI service quota is exhausted. Please try again later.",
            ),
        )

    @app.exception_handler(LLMConfigError)
    async def _handle_config(request: Request, exc: LLMConfigError) -> JSONResponse:
        logger.error("LLM configuration error: %s", exc)
        return JSONResponse(
            status_code=502,
            content=_error_body(
                "llm_config_error",
                "AI service is misconfigured on the server.",
            ),
        )

    @app.exception_handler(LLMTimeoutError)
    async def _handle_timeout(request: Request, exc: LLMTimeoutError) -> JSONResponse:
        logger.warning("LLM timeout: %s", exc)
        return JSONResponse(
            status_code=504,
            content=_error_body(
                "llm_timeout",
                "The AI service did not respond in time. Please try again.",
            ),
        )

    @app.exception_handler(LLMError)
    async def _handle_llm_error(request: Request, exc: LLMError) -> JSONResponse:
        logger.warning("LLM error: %s", exc)
        return JSONResponse(
            status_code=504,
            content=_error_body(
                "llm_error",
                "An error occurred while contacting the AI service.",
            ),
        )
