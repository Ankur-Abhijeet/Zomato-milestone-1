"""API smoke tests for POST /api/v1/recommendations — Phase 6.

Groq is mocked via the conftest.py fixture — no real API calls.
"""

from __future__ import annotations

URL = "/api/v1/recommendations"

VALID_BODY = {
    "location": "Koramangala",
    "budget": "medium",
    "min_rating": 3.0,
    "top_k": 5,
}


class TestValidation:
    def test_missing_location_returns_422(self, client):
        r = client.post(URL, json={"budget": "medium"})
        assert r.status_code == 422

    def test_invalid_budget_returns_422(self, client):
        r = client.post(URL, json={"location": "Bangalore", "budget": "super-expensive"})
        assert r.status_code == 422

    def test_negative_rating_returns_422(self, client):
        r = client.post(URL, json={"location": "Bangalore", "min_rating": -1.0})
        assert r.status_code == 422

    def test_top_k_zero_returns_422(self, client):
        r = client.post(URL, json={"location": "Bangalore", "top_k": 0})
        assert r.status_code == 422


class TestSuccessResponse:
    def test_status_200(self, client):
        r = client.post(URL, json=VALID_BODY)
        assert r.status_code == 200

    def test_response_shape(self, client):
        data = client.post(URL, json=VALID_BODY).json()
        assert "recommendations" in data
        assert "filter_stats" in data
        assert "dedup_removed" in data
        assert "used_fallback" in data
        assert "skip_llm" in data

    def test_filter_stats_keys(self, client):
        data = client.post(URL, json=VALID_BODY).json()
        stats = data["filter_stats"]
        assert stats is not None
        for key in ("initial", "after_location", "after_rating", "after_budget",
                    "after_cuisine", "capped_for_llm"):
            assert key in stats, f"Missing filter_stats key: {key}"

    def test_recommendations_list(self, client):
        data = client.post(URL, json=VALID_BODY).json()
        recs = data["recommendations"]
        assert isinstance(recs, list)
        assert len(recs) > 0

    def test_recommendation_item_fields(self, client):
        recs = client.post(URL, json=VALID_BODY).json()["recommendations"]
        item = recs[0]
        for field in ("rank", "id", "name", "cuisine", "location", "explanation",
                      "is_ai_generated"):
            assert field in item, f"Missing recommendation field: {field}"

    def test_dedup_removed_is_integer(self, client):
        data = client.post(URL, json=VALID_BODY).json()
        assert isinstance(data["dedup_removed"], int)
        assert data["dedup_removed"] >= 0

    def test_has_request_id_header(self, client):
        r = client.post(URL, json=VALID_BODY)
        assert "x-request-id" in r.headers

    def test_cuisines_optional(self, client):
        body = {**VALID_BODY, "cuisines": []}
        r = client.post(URL, json=body)
        assert r.status_code == 200

    def test_additional_optional(self, client):
        body = {**VALID_BODY, "additional": "good for families"}
        r = client.post(URL, json=body)
        assert r.status_code == 200

    def test_empty_location_returns_422(self, client):
        r = client.post(URL, json={"location": "", "budget": "medium"})
        assert r.status_code == 422
