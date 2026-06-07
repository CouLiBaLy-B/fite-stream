"""Tests for API middleware — rate limiter, auth, metrics."""

import pytest

from fitstream.api.middleware import APIKeyAuth, APIMetrics, RateLimiter


class TestRateLimiter:
    def test_allows_under_limit(self):
        limiter = RateLimiter(requests_per_minute=10, burst=20)
        for _ in range(10):
            assert limiter.allow("client1") is True

    def test_blocks_over_burst(self):
        limiter = RateLimiter(requests_per_minute=5, burst=3)
        for _ in range(3):
            limiter.allow("client2")
        assert limiter.allow("client2") is False

    def test_different_clients_independent(self):
        limiter = RateLimiter(requests_per_minute=5, burst=2)
        limiter.allow("a")
        limiter.allow("a")
        assert limiter.allow("a") is False
        assert limiter.allow("b") is True  # different client

    def test_generation_limit(self):
        limiter = RateLimiter(generation_per_minute=2)
        assert limiter.allow_generation("c") is True
        assert limiter.allow_generation("c") is True
        assert limiter.allow_generation("c") is False

    def test_get_remaining(self):
        limiter = RateLimiter(requests_per_minute=10, generation_per_minute=3)
        limiter.allow("d")
        limiter.allow_generation("d")

        remaining = limiter.get_remaining("d")
        assert remaining["requests_remaining"] == 9
        assert remaining["generation_remaining"] == 2


class TestAPIKeyAuth:
    def test_disabled_always_passes(self):
        auth = APIKeyAuth(enabled=False)
        assert auth.verify(None) is True
        assert auth.verify("anything") is True

    def test_enabled_requires_key(self):
        auth = APIKeyAuth(keys=["secret123"], enabled=True)
        assert auth.verify(None) is False
        assert auth.verify("wrong") is False
        assert auth.verify("secret123") is True

    def test_multiple_keys(self):
        auth = APIKeyAuth(keys=["key1", "key2", "key3"], enabled=True)
        assert auth.verify("key1") is True
        assert auth.verify("key2") is True
        assert auth.verify("key4") is False

    def test_add_key(self):
        auth = APIKeyAuth(keys=["original"], enabled=True)
        assert auth.verify("newkey") is False
        auth.add_key("newkey")
        assert auth.verify("newkey") is True

    def test_revoke_key(self):
        auth = APIKeyAuth(keys=["revokable"], enabled=True)
        assert auth.verify("revokable") is True
        auth.revoke_key("revokable")
        assert auth.verify("revokable") is False

    def test_keys_stored_as_hashes(self):
        auth = APIKeyAuth(keys=["secret"], enabled=True)
        # The actual key should not be stored
        assert "secret" not in str(auth._key_hashes)


class TestAPIMetrics:
    def test_record_request(self):
        m = APIMetrics()
        m.record_request("/api/v1/animate", 0.5)
        m.record_request("/api/v1/animate", 0.3)
        m.record_request("/api/v1/story", 1.0, error=True)

        assert m.total_requests == 3
        assert m.total_errors == 1
        assert m.endpoint_counts["/api/v1/animate"] == 2

    def test_record_generation(self):
        m = APIMetrics()
        m.record_generation("animate", 42.0)
        m.record_generation("story", 120.0)
        m.record_generation("animate", 38.0)

        assert m.total_generations == 3
        assert m.generations_by_type["animate"] == 2
        assert m.generations_by_type["story"] == 1

    def test_get_summary(self):
        m = APIMetrics()
        m.record_request("/test", 0.1)
        m.record_generation("animate", 50.0)

        summary = m.get_summary()
        assert summary["total_requests"] == 1
        assert summary["total_generations"] == 1
        assert "uptime_seconds" in summary
        assert "error_rate" in summary

    def test_latency_stats(self):
        m = APIMetrics()
        for i in range(100):
            m.record_request("/api/v1/test", 0.01 * (i + 1))

        summary = m.get_summary()
        latencies = summary["endpoint_latencies"].get("/api/v1/test", {})
        assert latencies["count"] == 100
        assert latencies["avg_ms"] > 0
        assert latencies["p95_ms"] > latencies["p50_ms"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
