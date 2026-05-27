"""Shared pytest fixtures for Phase 6 tests."""

from __future__ import annotations

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.main import create_app
from config.settings import Settings, get_settings
from models.recommendation import RecommendationItem, RecommendationResult


# ── Settings override ─────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Settings with a dummy GROQ_API_KEY so validation passes."""
    return Settings(GROQ_API_KEY="test-key-not-real")


# ── Canned domain result (no Groq call) ──────────────────────────────────────

def _make_canned_result() -> RecommendationResult:
    return RecommendationResult(
        summary="Test summary",
        recommendations=[
            RecommendationItem(
                rank=1,
                restaurant_id="abc123",
                name="Test Bistro",
                cuisine="Italian",
                rating=4.5,
                estimated_cost="1,200",
                location="Koramangala, Bangalore",
                explanation="Great test restaurant.",
                is_ai_generated=True,
            ),
            RecommendationItem(
                rank=2,
                restaurant_id="def456",
                name="Curry House",
                cuisine="Indian",
                rating=4.2,
                estimated_cost="600",
                location="Koramangala, Bangalore",
                explanation="Excellent curry.",
                is_ai_generated=True,
            ),
        ],
        used_fallback=False,
        fallback_reason=None,
        top_k=5,
    )


# ── App + TestClient fixtures ─────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app_with_repo():
    """
    App with the real repository loaded from the Parquet cache.
    The Groq client is mocked so no real API calls happen.
    """
    with patch(
        "services.recommendation_engine.RecommendationEngine.recommend",
        return_value=_make_canned_result(),
    ):
        app = create_app()
        # Force-load the repo synchronously for TestClient
        from data.repository import RestaurantRepository
        settings = get_settings()
        repo = RestaurantRepository(settings)
        repo.load()
        app.state.repository = repo
        app.state.repository_ready = True
        yield app


@pytest.fixture(scope="session")
def client(app_with_repo) -> Generator[TestClient, None, None]:
    """Synchronous TestClient wrapping the fully-loaded app."""
    with TestClient(app_with_repo, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture()
def unready_client() -> Generator[TestClient, None, None]:
    """TestClient where the dataset load is skipped → /ready returns 503."""
    from unittest.mock import patch as _patch
    with _patch("data.repository.RestaurantRepository.load", return_value=None):
        app = create_app()
        with TestClient(app, raise_server_exceptions=False) as c:
            app.state.repository_ready = False
            yield c
