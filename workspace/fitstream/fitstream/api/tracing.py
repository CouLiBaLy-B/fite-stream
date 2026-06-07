"""
FitStream Request Tracing
Correlation IDs and structured context for every request.

Every request gets a unique trace_id that flows through:
  - HTTP response headers (X-Trace-Id)
  - Log entries (via loguru context)
  - Job metadata
  - Error reports

This enables end-to-end tracing across:
  API request → background job → pipeline → model → video output
"""

import uuid
import time
from contextvars import ContextVar
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


# Context variable holding the current request's trace ID
_trace_id: ContextVar[str] = ContextVar("trace_id", default="")
_request_start: ContextVar[float] = ContextVar("request_start", default=0.0)


def get_trace_id() -> str:
    """Get the current request's trace ID."""
    return _trace_id.get("")


def generate_trace_id() -> str:
    """Generate a new trace ID."""
    return uuid.uuid4().hex[:16]


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Assigns a unique trace ID to every request.
    
    - Sets X-Trace-Id response header
    - Propagates incoming X-Trace-Id if present (distributed tracing)
    - Adds trace_id to loguru context
    - Measures total request duration
    """
    
    async def dispatch(self, request: Request, call_next):
        # Use incoming trace ID or generate new one
        trace_id = request.headers.get("X-Trace-Id", "") or generate_trace_id()
        
        # Set context variables
        token_trace = _trace_id.set(trace_id)
        token_start = _request_start.set(time.time())
        
        try:
            # Add trace context to loguru
            with logger.contextualize(trace_id=trace_id):
                response = await call_next(request)
            
            # Add trace headers to response
            response.headers["X-Trace-Id"] = trace_id
            response.headers["X-Request-Duration-Ms"] = str(
                int((time.time() - _request_start.get(0)) * 1000)
            )
            
            return response
        
        finally:
            _trace_id.reset(token_trace)
            _request_start.reset(token_start)
