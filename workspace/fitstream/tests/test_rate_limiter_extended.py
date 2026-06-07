"""Tests for RateLimiter — including memory leak fix verification."""

import time

from fitstream.api.middleware import APIKeyAuth, APIMetrics, RateLimiter


class TestRateLimiterMemoryLeak:
    """Verify that the memory leak fix works correctly."""

    def test_cleanup_empty_entries_removes_stale_clients(self) -> None:
        limiter = RateLimiter(requests_per_minute=30, burst=50)
        limiter.allow("client_old")
        # Simulate time passing by manually clearing timestamps
        limiter._requests["client_old"].clear()
        # Force cleanup of empty entries
        limiter._cleanup_empty_entries()
        assert "client_old" not in limiter._requests

    def test_cleanup_keeps_active_clients(self) -> None:
        limiter = RateLimiter(requests_per_minute=30, burst=50)
        limiter.allow("client_active")
        limiter._cleanup_empty_entries()
        assert "client_active" in limiter._requests

    def test_generation_cleanup_removes_stale(self) -> None:
        limiter = RateLimiter(generation_per_minute=5)
        limiter.allow_generation("gen_client")
        limiter._gen_requests["gen_client"].clear()
        limiter._cleanup_empty_entries()
        assert "gen_client" not in limiter._gen_requests

    def test_get_remaining_triggers_cleanup(self) -> None:
        limiter = RateLimiter(requests_per_minute=30, burst=50)
        limiter.allow("will_be_cleared")
        limiter._requests["will_be_cleared"].clear()
        remaining = limiter.get_remaining("will_be_cleared")
        # get_remaining calls _cleanup_empty_entries internally
        assert "will_be_cleared" not in limiter._requests
        assert remaining["requests_remaining"] == limiter.rpm


class TestRateLimiterBasic:
    """Basic rate limiter functionality."""

    def test_allow_within_limit(self) -> None:
        limiter = RateLimiter(requests_per_minute=10, burst=20)
        for _ in range(15):
            assert limiter.allow("c1") is True

    def test_blocks_over_burst(self) -> None:
        limiter = RateLimiter(requests_per_minute=10, burst=5)
        for _ in range(5):
            assert limiter.allow("c2") is True
        assert limiter.allow("c2") is False

    def test_different_clients_independent(self) -> None:
        limiter = RateLimiter(requests_per_minute=10, burst=3)
        for _ in range(3):
            limiter.allow("a")
        assert limiter.allow("b") is True

    def test_generation_limit(self) -> None:
        limiter = RateLimiter(generation_per_minute=3)
        for _ in range(3):
            assert limiter.allow_generation("c") is True
        assert limiter.allow_generation("c") is False

    def test_get_remaining(self) -> None:
        limiter = RateLimiter(requests_per_minute=10, burst=20)
        limiter.allow("d")
        remaining = limiter.get_remaining("d")
        assert remaining["requests_remaining"] == 9
        assert "reset_in_seconds" in remaining


class TestRateLimiterExpiry:
    """Test that expired timestamps are properly cleaned."""

    def test_expired_timestamps_cleaned(self) -> None:
        limiter = RateLimiter(requests_per_minute=10, burst=20)
        # Manually inject an old timestamp
        limiter._requests["expired"] = [time.time() - 120]  # 2 min ago
        assert limiter.allow("expired") is True
        assert len(limiter._requests["expired"]) == 1  # Old one removed


class TestAPIKeyAuth:
    """API key authentication tests."""

    def test_disabled_allows_all(self) -> None:
        auth = APIKeyAuth(enabled=False)
        assert auth.verify(None) is True
        assert auth.verify("anything") is True

    def test_enabled_rejects_missing_key(self) -> None:
        auth = APIKeyAuth(keys=["secret"], enabled=True)
        assert auth.verify(None) is False
        assert auth.verify("") is False

    def test_enabled_verifies_valid_key(self) -> None:
        auth = APIKeyAuth(keys=["my-secret-key"], enabled=True)
        assert auth.verify("my-secret-key") is True

    def test_enabled_rejects_invalid_key(self) -> None:
        auth = APIKeyAuth(keys=["correct"], enabled=True)
        assert auth.verify("wrong") is False

    def test_add_revoke_key(self) -> None:
        auth = APIKeyAuth(enabled=True)
        auth.add_key("new-key")
        assert auth.verify("new-key") is True
        auth.revoke_key("new-key")
        assert auth.verify("new-key") is False


class TestAPIMetrics:
    """API metrics collection tests."""

    def test_initial_state(self) -> None:
        m = APIMetrics()
        assert m.total_requests == 0
        assert m.total_errors == 0

    def test_record_request(self) -> None:
        m = APIMetrics()
        m.record_request("/test", 0.1, error=False)
        assert m.total_requests == 1
        assert m.total_errors == 0

    def test_record_error(self) -> None:
        m = APIMetrics()
        m.record_request("/bad", 0.5, error=True)
        assert m.total_requests == 1
        assert m.total_errors == 1

    def test_record_generation(self) -> None:
        m = APIMetrics()
        m.record_generation("animate", 10.0)
        assert m.total_generations == 1
        assert m.generations_by_type["animate"] == 1

    def test_get_summary(self) -> None:
        m = APIMetrics()
        m.record_request("/test", 0.2)
        summary = m.get_summary()
        assert "total_requests" in summary
        assert "uptime_seconds" in summary
        assert "error_rate" in summary
        assert summary["total_requests"] == 1

    def test_endpoint_latencies_limited(self) -> None:
        m = APIMetrics()
        for _ in range(1200):
            m.record_request("/spam", 0.01)
        assert len(m.endpoint_latencies["/spam"]) <= 1000
