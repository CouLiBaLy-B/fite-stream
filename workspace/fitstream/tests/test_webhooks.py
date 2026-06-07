"""Tests for webhook manager."""

import pytest
from fitstream.core.webhooks import WebhookManager, WebhookEndpoint


class TestWebhookManager:
    def setup_method(self):
        self.wm = WebhookManager()

    def test_register(self):
        eid = self.wm.register("https://example.com/hook")
        assert eid is not None
        assert len(eid) == 12

    def test_register_with_events(self):
        eid = self.wm.register("https://example.com/hook",
                                events=["completed"])
        endpoints = self.wm.list_endpoints()
        assert len(endpoints) == 1
        assert "completed" in endpoints[0]["events"]
        assert "failed" not in endpoints[0]["events"]

    def test_register_invalid_events(self):
        with pytest.raises(ValueError, match="Invalid events"):
            self.wm.register("https://example.com/hook",
                              events=["invalid_event"])

    def test_unregister(self):
        eid = self.wm.register("https://example.com/hook")
        assert self.wm.unregister(eid) is True
        assert self.wm.unregister(eid) is False  # already removed

    def test_list_endpoints(self):
        self.wm.register("https://a.com/hook")
        self.wm.register("https://b.com/hook")
        endpoints = self.wm.list_endpoints()
        assert len(endpoints) == 2

    def test_list_endpoint_fields(self):
        self.wm.register("https://test.com/hook", events=["completed"])
        ep = self.wm.list_endpoints()[0]
        assert "id" in ep
        assert "url" in ep
        assert ep["url"] == "https://test.com/hook"
        assert "active" in ep
        assert "total_sent" in ep

    def test_valid_events(self):
        assert "completed" in WebhookManager.VALID_EVENTS
        assert "failed" in WebhookManager.VALID_EVENTS
        assert "processing" in WebhookManager.VALID_EVENTS
        assert "progress" in WebhookManager.VALID_EVENTS
        assert "queued" in WebhookManager.VALID_EVENTS


class TestWebhookEndpoint:
    def test_defaults(self):
        ep = WebhookEndpoint(url="https://test.com")
        assert ep.active is True
        assert "completed" in ep.events
        assert "failed" in ep.events
        assert ep.total_sent == 0

    def test_with_secret(self):
        ep = WebhookEndpoint(url="https://test.com", secret="mysecret")
        assert ep.secret == "mysecret"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
