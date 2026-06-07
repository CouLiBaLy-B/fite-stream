"""
FitStream Webhook Notifications
Send HTTP callbacks when jobs complete or fail.

Usage:
    manager = WebhookManager()
    manager.register("https://your-app.com/webhook", events=["completed", "failed"])
    
    # When a job finishes:
    await manager.notify("completed", job_id="abc", video_url="/api/v1/jobs/abc/video")
"""

import time
import hmac
import hashlib
import json
import asyncio
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class WebhookEndpoint:
    """A registered webhook endpoint."""
    url: str
    events: Set[str] = field(default_factory=lambda: {"completed", "failed"})
    secret: str = ""             # HMAC secret for signature verification
    active: bool = True
    created_at: float = field(default_factory=time.time)
    # Stats
    total_sent: int = 0
    total_failed: int = 0
    last_sent_at: Optional[float] = None
    last_error: Optional[str] = None


class WebhookManager:
    """
    Manages webhook registrations and notifications.
    
    Features:
    - Register/unregister endpoints
    - Event filtering (only notify on specific events)
    - HMAC-SHA256 signatures for security
    - Retry with exponential backoff
    - Async delivery
    """
    
    VALID_EVENTS = {"queued", "processing", "completed", "failed", "progress"}
    
    def __init__(self, max_retries: int = 3, timeout: float = 10.0) -> None:
        self._endpoints: Dict[str, WebhookEndpoint] = {}
        self.max_retries = max_retries
        self.timeout = timeout
    
    def register(
        self,
        url: str,
        events: Optional[List[str]] = None,
        secret: str = "",
    ) -> str:
        """
        Register a webhook endpoint.
        Returns the endpoint ID.
        """
        # Validate events
        event_set = set(events or ["completed", "failed"])
        invalid = event_set - self.VALID_EVENTS
        if invalid:
            raise ValueError(f"Invalid events: {invalid}. Valid: {self.VALID_EVENTS}")
        
        endpoint = WebhookEndpoint(url=url, events=event_set, secret=secret)
        
        # Use URL hash as ID
        endpoint_id = hashlib.md5(url.encode()).hexdigest()[:12]
        self._endpoints[endpoint_id] = endpoint
        
        logger.info(f"🔔 Webhook registered: {url} (events: {event_set})")
        return endpoint_id
    
    def unregister(self, endpoint_id: str) -> bool:
        if endpoint_id in self._endpoints:
            del self._endpoints[endpoint_id]
            return True
        return False
    
    def list_endpoints(self) -> List[dict]:
        """Remove a webhook endpoint."""
        """List all registered webhooks."""
        return [
            {
                "id": eid,
                "url": ep.url,
                "events": sorted(ep.events),
                "active": ep.active,
                "total_sent": ep.total_sent,
                "total_failed": ep.total_failed,
                "last_error": ep.last_error,
            }
            for eid, ep in self._endpoints.items()
        ]
    
    async def notify(
        self,
        event: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send a notification to all endpoints subscribed to this event.
        Non-blocking: failures are logged but don't raise exceptions.
        """
        if event not in self.VALID_EVENTS:
            logger.warning(f"Unknown webhook event: {event}")
            return
        
        data = {
            "event": event,
            "timestamp": time.time(),
            **(payload or {}),
        }
        
        for endpoint_id, endpoint in self._endpoints.items():
            if not endpoint.active:
                continue
            if event not in endpoint.events:
                continue
            
            # Fire and forget (don't block the caller)
            asyncio.create_task(
                self._deliver(endpoint_id, endpoint, data)
            )
    
    async def _deliver(
        self,
        endpoint_id: str,
        endpoint: WebhookEndpoint,
        data: dict,
    ) -> None:
        """Deliver a webhook with retries."""
        body = json.dumps(data, default=str)
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FitStream-Webhook/1.0",
            "X-FitStream-Event": data.get("event", ""),
        }
        
        # Add HMAC signature if secret is set
        if endpoint.secret:
            signature = hmac.new(
                endpoint.secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-FitStream-Signature"] = f"sha256={signature}"
        
        for attempt in range(self.max_retries):
            try:
                import httpx
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        endpoint.url,
                        content=body,
                        headers=headers,
                    )
                
                if response.status_code < 400:
                    endpoint.total_sent += 1
                    endpoint.last_sent_at = time.time()
                    endpoint.last_error = None
                    logger.debug(f"🔔 Webhook delivered: {endpoint.url} ({data.get('event')})")
                    return
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
                    
            except ImportError:
                # httpx not installed — use urllib as fallback
                try:
                    import urllib.request
                    req = urllib.request.Request(
                        endpoint.url,
                        data=body.encode(),
                        headers=headers,
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                        if resp.status < 400:
                            endpoint.total_sent += 1
                            endpoint.last_sent_at = time.time()
                            return
                except (OSError, ValueError, KeyError) as e:
                    endpoint.last_error = str(e)
                    
            except (OSError, ValueError, KeyError) as e:
                endpoint.last_error = str(e)
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt  # exponential backoff
                    logger.warning(
                        f"⚠️ Webhook retry {attempt + 1}/{self.max_retries} "
                        f"for {endpoint.url}: {e} (waiting {wait}s)"
                    )
                    await asyncio.sleep(wait)
        
        # All retries failed
        endpoint.total_failed += 1
        logger.error(f"❌ Webhook failed after {self.max_retries} retries: {endpoint.url}")


# Global instance
webhook_manager = WebhookManager()
