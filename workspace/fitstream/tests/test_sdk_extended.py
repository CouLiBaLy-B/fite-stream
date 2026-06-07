"""Tests for the Python SDK client."""

from fitstream.sdk import FitStreamClient


class TestSDKClientInit:
    """SDK client initialization."""

    def test_default_init(self) -> None:
        client = FitStreamClient()
        assert client.base_url == "http://localhost:8000"
        assert client.api_key is None

    def test_custom_base_url(self) -> None:
        client = FitStreamClient(base_url="https://api.example.com")
        assert client.base_url == "https://api.example.com"

    def test_with_api_key(self) -> None:
        client = FitStreamClient(api_key="sk-test123")
        assert client.api_key == "sk-test123"

    def test_default_timeout(self) -> None:
        client = FitStreamClient()
        assert client.timeout > 0

    def test_custom_timeout(self) -> None:
        client = FitStreamClient(timeout=30)
        assert client.timeout == 30
