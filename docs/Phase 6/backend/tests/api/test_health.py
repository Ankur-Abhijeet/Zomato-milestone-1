"""API tests for health / readiness probes — Phase 6."""

from __future__ import annotations


class TestHealth:
    def test_liveness_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_liveness_has_request_id(self, client):
        r = client.get("/health")
        assert "x-request-id" in r.headers

    def test_request_id_is_stable_when_provided(self, client):
        """Upstream request ID must be echoed back unchanged."""
        custom_id = "my-trace-123"
        r = client.get("/health", headers={"X-Request-ID": custom_id})
        assert r.headers.get("x-request-id") == custom_id


class TestReady:
    def test_ready_after_load(self, client):
        r = client.get("/ready")
        assert r.status_code == 200
        assert r.json() == {"status": "ready"}

    def test_not_ready_before_load(self, unready_client):
        r = unready_client.get("/ready")
        assert r.status_code == 503
