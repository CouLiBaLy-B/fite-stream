"""
FitStream API Middleware
Rate limiting, authentication, metrics, and request logging.
"""

import time
import hashlib
from collections import defaultdict
from typing import Optional, Dict, Callable
from dataclasses import dataclass, field
from loguru import logger

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


# ============================================================
# Rate Limiter
# ============================================================

class RateLimiter:
    """
    In-memory sliding window rate limiter.
    
    Usage:
        limiter = RateLimiter(requests_per_minute=10, burst=20)
        
        @app.middleware("http")
        async def rate_limit(request, call_next):
            client_ip = request.client.host
            if not limiter.allow(client_ip):
                return JSONResponse({"error": "Rate limit exceeded"}, 429)
            return await call_next(request)
    """
    
    def __init__(
        self,
        requests_per_minute: int = 30,
        burst: int = 50,
        generation_per_minute: int = 5,
    ) -> None:
        self.rpm = requests_per_minute
        self.burst = burst
        self.gen_rpm = generation_per_minute
        
        self._requests: Dict[str, list] = defaultdict(list)
        self._gen_requests: Dict[str, list] = defaultdict(list)
    
    def _cleanup(self, timestamps: list, window: float = 60.0) -> None:
        """Remove expired timestamps from the list."""
        cutoff = time.time() - window
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)
    
    def _cleanup_empty_entries(self) -> None:
        """Periodically remove client entries that have no active timestamps."""
        for bucket in [self._requests, self._gen_requests]:
            empty_clients = [
                cid for cid, ts in list(bucket.items()) if not ts
            ]
            for cid in empty_clients:
                del bucket[cid]
    
    def allow(self, client_id: str) -> bool:
        now = time.time()
        timestamps = self._requests[client_id]
        self._cleanup(timestamps)
        
        if len(timestamps) >= self.burst:
            return False
        
        timestamps.append(now)
        return True
    
    def allow_generation(self, client_id: str) -> bool:
        now = time.time()
        timestamps = self._gen_requests[client_id]
        self._cleanup(timestamps)
        
        if len(timestamps) >= self.gen_rpm:
            return False
        
        timestamps.append(now)
        return True
    
    def get_remaining(self, client_id: str) -> Dict[str, int]:
        self._cleanup(self._requests[client_id])
        self._cleanup(self._gen_requests[client_id])
        # Clean up empty entries to prevent memory leak
        self._cleanup_empty_entries()
        
        return {
            "requests_remaining": max(0, self.rpm - len(self._requests[client_id])),
            "generation_remaining": max(0, self.gen_rpm - len(self._gen_requests[client_id])),
            "reset_in_seconds": 60,
        }


# ============================================================
# API Key Authentication
# ============================================================

class APIKeyAuth:
    """
    Simple API key authentication.
    
    Keys are stored as SHA-256 hashes for security.
    Set FITSTREAM_API_KEYS env var with comma-separated keys.
    
    Usage:
        auth = APIKeyAuth(keys=["key1", "key2"])
        
        # In endpoint:
        api_key = request.headers.get("X-API-Key")
        if not auth.verify(api_key):
            raise HTTPException(401, "Invalid API key")
    """
    
    def __init__(self, keys: Optional[list] = None, enabled: bool = False) -> None:
        self.enabled = enabled
        self._key_hashes = set()
        
        if keys:
            for key in keys:
                self._key_hashes.add(self._hash(key))
    
    @staticmethod
    def _hash(key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()
    
    def verify(self, key: Optional[str]) -> bool:
        if not self.enabled:
            return True
        if not key:
            return False
        return self._hash(key) in self._key_hashes
    
    def add_key(self, key: str) -> None:
        self._key_hashes.add(self._hash(key))
    
    def revoke_key(self, key: str) -> None:
        self._key_hashes.discard(self._hash(key))


# ============================================================
# Metrics Collector
# ============================================================

@dataclass
class APIMetrics:
    """
    Lightweight in-memory API metrics.
    Tracks request counts, latencies, and error rates.
    """
    total_requests: int = 0
    total_errors: int = 0
    total_generations: int = 0
    total_generation_time: float = 0.0
    
    # Per-endpoint counters
    endpoint_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    endpoint_errors: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    endpoint_latencies: Dict[str, list] = field(default_factory=lambda: defaultdict(list))
    
    # Generation stats
    generations_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    _start_time: float = field(default_factory=time.time)
    
    def record_request(self, endpoint: str, latency: float, error: bool = False) -> None:
        self.total_requests += 1
        self.endpoint_counts[endpoint] += 1
        
        # Keep only last 1000 latencies per endpoint
        latencies = self.endpoint_latencies[endpoint]
        latencies.append(latency)
        if len(latencies) > 1000:
            self.endpoint_latencies[endpoint] = latencies[-500:]
        
        if error:
            self.total_errors += 1
            self.endpoint_errors[endpoint] += 1
    
    def record_generation(self, gen_type: str, generation_time: float) -> None:
        self.total_generations += 1
        self.total_generation_time += generation_time
        self.generations_by_type[gen_type] += 1
    
    def get_summary(self) -> dict:
        """Record a completed generation."""
        """Get a summary of all metrics."""
        uptime = time.time() - self._start_time
        
        # Calculate average latencies
        avg_latencies = {}
        for endpoint, latencies in self.endpoint_latencies.items():
            if latencies:
                avg_latencies[endpoint] = {
                    "avg_ms": sum(latencies) / len(latencies) * 1000,
                    "p50_ms": sorted(latencies)[len(latencies) // 2] * 1000,
                    "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] * 1000 if len(latencies) > 1 else 0,
                    "count": len(latencies),
                }
        
        return {
            "uptime_seconds": uptime,
            "uptime_human": f"{uptime / 3600:.1f}h",
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
            "error_rate": self.total_errors / max(1, self.total_requests),
            "requests_per_minute": self.total_requests / max(1, uptime / 60),
            "total_generations": self.total_generations,
            "avg_generation_time": (
                self.total_generation_time / max(1, self.total_generations)
            ),
            "generations_by_type": dict(self.generations_by_type),
            "endpoint_latencies": avg_latencies,
        }


# ============================================================
# Request Logging Middleware
# ============================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing."""
    
    def __init__(self, app, metrics: Optional[APIMetrics] = None) -> None:
        super().__init__(app)
        self.metrics = metrics or APIMetrics()
    
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        
        # Skip logging for static files and health checks
        path = request.url.path
        skip_log = path in ("/health", "/gpu", "/favicon.ico")
        
        try:
            response = await call_next(request)
            latency = time.time() - start
            
            is_error = response.status_code >= 400
            self.metrics.record_request(path, latency, error=is_error)
            
            if not skip_log:
                status_emoji = "✅" if response.status_code < 400 else "⚠️" if response.status_code < 500 else "❌"
                logger.info(
                    f"{status_emoji} {request.method} {path} → {response.status_code} "
                    f"({latency*1000:.0f}ms)"
                )
            
            # Add rate limit headers
            client_ip = request.client.host if request.client else "unknown"
            response.headers["X-Request-Duration-Ms"] = f"{latency*1000:.0f}"
            
            return response
            
        except (RuntimeError, OSError) as e:
            latency = time.time() - start
            self.metrics.record_request(path, latency, error=True)
            logger.error(f"❌ {request.method} {path} → 500 ({e})")
            raise


# Global instances
rate_limiter = RateLimiter()
api_auth = APIKeyAuth()
metrics = APIMetrics()
