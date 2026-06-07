"""Tests for request tracing middleware."""

import pytest
from fitstream.api.tracing import (
    TracingMiddleware,
    get_trace_id,
    generate_trace_id,
    _trace_id,
    _request_start,
)


class TestTracingBasics:
    """Basic tracing functionality."""

    def test_generate_trace_id_format(self) -> None:
        tid = generate_trace_id()
        assert isinstance(tid, str)
        assert len(tid) == 16
        assert tid != ""  # Not empty hex

    def test_generate_trace_id_unique(self) -> None:
        ids = {generate_trace_id() for _ in range(100)}
        assert len(ids) == 100  # All unique

    def test_generate_trace_id_is_hex(self) -> None:
        tid = generate_trace_id()
        int(tid, 16)  # Should not raise ValueError

    def test_get_trace_id_default_empty(self) -> None:
        assert get_trace_id() == ""

    def test_context_var_isolation(self) -> None:
        token = _trace_id.set("trace-123")
        assert get_trace_id() == "trace-123"
        _trace_id.reset(token)
        assert get_trace_id() == ""


class TestTracingContext:
    """Context variable behavior."""

    def test_trace_id_doesnt_leak_between_tests(self) -> None:
        # Default should be empty in clean context
        assert get_trace_id() == ""

    def test_request_start_context(self) -> None:
        import time
        token = _request_start.set(time.time())
        start = _request_start.get(0)
        assert start > 0
        _request_start.reset(token)

    def test_set_and_reset(self) -> None:
        token = _trace_id.set("abc123def456")
        assert get_trace_id() == "abc123def456"
        _trace_id.reset(token)
        assert get_trace_id() == ""
