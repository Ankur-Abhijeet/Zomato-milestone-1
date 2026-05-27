"""API tests for GET /api/v1/meta — Phase 6."""

from __future__ import annotations


class TestMeta:
    def test_status_ok(self, client):
        r = client.get("/api/v1/meta")
        assert r.status_code == 200

    def test_budget_bands_keys(self, client):
        data = client.get("/api/v1/meta").json()
        assert set(data["budget_bands"].keys()) == {"low", "medium", "high"}

    def test_budget_low_description(self, client):
        data = client.get("/api/v1/meta").json()
        assert "500" in data["budget_bands"]["low"]

    def test_budget_medium_description(self, client):
        data = client.get("/api/v1/meta").json()
        assert "1,500" in data["budget_bands"]["medium"]

    def test_defaults_present(self, client):
        data = client.get("/api/v1/meta").json()
        assert "default_top_k" in data
        assert "default_min_rating" in data
        assert "default_budget" in data
        assert data["default_budget"] in ("low", "medium", "high")

    def test_example_locations_non_empty(self, client):
        data = client.get("/api/v1/meta").json()
        assert isinstance(data["example_locations"], list)
        assert len(data["example_locations"]) > 0
