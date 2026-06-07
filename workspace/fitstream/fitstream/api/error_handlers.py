"""
FitStream Error Handlers
Global exception handlers for the FastAPI application.

Converts FitStreamError subclasses into structured JSON responses
with proper HTTP status codes, error codes, and retryable flags.
"""

import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from fitstream.core.errors import FitStreamError


def register_error_handlers(app: FastAPI) -> None:

    @app.exception_handler(FitStreamError)
    async def fitstream_error_handler(request: Request, exc: FitStreamError) -> JSONResponse:
        """Handle all FitStreamError subclasses with structured responses."""
        log_level = "warning" if exc.status_code < 500 else "error"
        getattr(logger, log_level)(
            f"{exc.error_code}: {exc.message}"
            + (f" | cause={exc.cause}" if exc.cause else "")
            + (f" | details={exc.details}" if exc.details else "")
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all FitStreamError subclasses with structured responses."""
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}:\n"
            + "".join(tb)
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred.",
                "retryable": False,
            },
        )
