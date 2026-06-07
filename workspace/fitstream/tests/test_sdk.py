"""Tests for the Python SDK client — no server needed for these tests."""

import pytest
from fitstream.sdk import FitStreamClient, SDKResult


class TestFitStreamClient:
    def test_init_default(self):
        client = FitStreamClient()
        assert client.base_url == "http://localhost:8000"
        assert client.api_key is None
    
    def test_init_custom(self):
        client = FitStreamClient("https://api.example.com", api_key="mykey")
        assert client.base_url == "https://api.example.com"
        assert client.api_key == "mykey"
    
    def test_trailing_slash_stripped(self):
        client = FitStreamClient("http://localhost:8000/")
        assert client.base_url == "http://localhost:8000"
    
    def test_headers_without_key(self):
        client = FitStreamClient()
        headers = client._headers()
        assert "User-Agent" in headers
        assert "X-API-Key" not in headers
    
    def test_headers_with_key(self):
        client = FitStreamClient(api_key="secret")
        headers = client._headers()
        assert headers["X-API-Key"] == "secret"


class TestSDKResult:
    def test_completed(self):
        r = SDKResult(job_id="abc", status="completed", video_url="/video.mp4")
        assert r.status == "completed"
        assert r.error is None
    
    def test_failed(self):
        r = SDKResult(job_id="abc", status="failed", error="GPU OOM")
        assert r.status == "failed"
        assert r.error == "GPU OOM"
    
    def test_timeout(self):
        r = SDKResult(job_id="abc", status="timeout", error="Timed out")
        assert r.status == "timeout"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
