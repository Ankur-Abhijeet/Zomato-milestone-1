"""Health and readiness probes (Phase 5a).

GET /health  — liveness: always 200 when the process is up.
GET /ready   — readiness: 200 only after the dataset has loaded successfully.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns 200 OK as long as the process is running.",
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Readiness probe",
    description="Returns 200 OK only after the restaurant dataset has been loaded.",
    responses={503: {"description": "Dataset not yet loaded"}},
)
async def ready(request: Request) -> HealthResponse:
    if not getattr(request.app.state, "repository_ready", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "not_ready",
                "message": "Dataset is still loading. Please retry in a moment.",
            },
        )
    return HealthResponse(status="ready")
