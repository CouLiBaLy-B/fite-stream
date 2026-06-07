"""Tests for the WebhookManager — realistic API surface."""

import pytest
from fitstream.core.webhooks import webhook_manager, WebhookEndpoint


class TestWebhookEndpoint:
    """WebhookEndpoint dataclass tests."""

    def test_default_events(self) -> None:
        ep = WebhookEndpoint(url="https://example.com/hook")
        assert ep.url == "https://example.com/hook"
        assert isinstance(ep.events, set)
        assert "completed" in ep.events
        assert "failed" in ep.events
        assert ep.secret == ""
        assert ep.active is True

    def test_with_custom_events(self) -> None:
        ep = WebhookEndpoint(url="https://x.com/hook", events={"queued", "processing"})
        assert ep.events == {"queued", "processing"}

    def test_with_secret(self) -> None:
        ep = WebhookEndpoint(url="https://x.com/hook", secret="hmac_secret")
        assert ep.secret == "hmac_secret"

    def test_inactive(self) -> None:
        ep = WebhookEndpoint(url="https://x.com/hook", active=False)
        assert ep.active is False


class TestWebhookManagerRegistration:
    """WebhookManager register/unregister."""

    def test_register_basic(self) -> None:
        eid = webhook_manager.register("https://example.com/webhook")
        assert eid is not None
        assert len(eid) > 0
        webhook_manager.unregister(eid)

    def test_register_with_events(self) -> None:
        eid = webhook_manager.register(
            "https://example.com/hook",
            events=["completed", "failed"],
        )
        assert eid is not None
        webhook_manager.unregister(eid)

    def test_unregister(self) -> None:
        eid = webhook_manager.register("https://example.com/unreg")
        assert webhook_manager.unregister(eid) is True

    def test_unregister_nonexistent(self) -> None:
        assert webhook_manager.unregister("fake-id") is False

    def test_list_endpoints_empty(self) -> None:
        endpoints = webhook_manager.list_endpoints()
        assert isinstance(endpoints, list)

    def test_list_endpoints_with_data(self) -> None:
        eid = webhook_manager.register("https://test.com/hook")
        endpoints = webhook_manager.list_endpoints()
        ep = next(e for e in endpoints if e["id"] == eid)
        assert ep["url"] == "https://test.com/hook"
        assert "events" in ep
        assert ep["active"] is True
        webhook_manager.unregister(eid)

    def test_unregister_removes_from_list(self) -> None:
        eid = webhook_manager.register("https://remove-me.com/hook")
        webhook_manager.unregister(eid)
        endpoints = webhook_manager.list_endpoints()
        ids = [e["id"] for e in endpoints]
        assert eid not in ids