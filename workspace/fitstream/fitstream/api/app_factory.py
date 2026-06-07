"""
FitStream Application Factory
Creates and configures the FastAPI application with proper dependency injection.

This replaces the monolithic server.py with a clean, testable factory pattern.

Usage:
    from fitstream.api.app_factory import create_app
    
    app = create_app()
    
    # Or with custom config for testing:
    app = create_app(config=test_config)
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from loguru import logger

from fitstream import __version__
from fitstream.api.middleware import RequestLoggingMiddleware, metrics
from fitstream.api.tracing import TracingMiddleware
from fitstream.api.websocket import ws_manager
from fitstream.api.mobile import mobile_router
from fitstream.api.error_handlers import register_error_handlers

# Import routers
from fitstream.api.routes.health import router as health_router
from fitstream.api.routes.generation import router as generation_router
from fitstream.api.routes.jobs import router as jobs_router
from fitstream.api.routes.admin import router as admin_router


def create_app() -> FastAPI:
    """
    Application factory — creates a fully configured FastAPI app.
    
    This follows the factory pattern for testability:
      - Dependencies are injected via FastAPI Depends()
      - No global mutable state
      - Each router handles its own domain
      - Middleware is configured centrally
    """
    
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> None:
        logger.info(f"🎬 FitStream API v{__version__} starting")
        yield
        logger.info("🎬 FitStream API shutting down gracefully")
    
    app = FastAPI(
        title="FitStream API",
        description="🎬 Animation Storytelling & Virtual Try-On API",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # ── Middleware ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: restrict in production via config
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware, metrics=metrics)
    app.add_middleware(TracingMiddleware)
    
    # ── Error handlers ──
    register_error_handlers(app)
    
    # ── Mount routers ──
    app.include_router(health_router)
    app.include_router(generation_router)
    app.include_router(jobs_router)
    app.include_router(admin_router)
    app.include_router(mobile_router, prefix="/m")
    
    # ── Root ──
    @app.get("/", tags=["Health"])
    async def root() -> dict:
        """Lifespan."""
        """Root."""
        return {"message": "🎬 FitStream API", "version": __version__, "docs": "/docs"}
    
    # ── WebSocket ──
    @app.websocket("/ws/jobs/{job_id}")
    async def websocket_progress(websocket: WebSocket, job_id: str) -> None:
        await ws_manager.connect(websocket, job_id)
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket, job_id)
        except Exception:
            ws_manager.disconnect(websocket, job_id)
    
    # ── Static frontend pages ──
    _frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    
    _pages = {
        "/app": "index.html",
        "/create": "create.html",
        "/gallery": "gallery.html",
        "/monitor": "monitor.html",
    }
    
    for route, filename in _pages.items():
        """Websocket progress."""
        filepath = _frontend_dir / filename
        # Create closure properly
        def _make_handler(p: Path):
            async def handler():
                """Handler."""
                if p.exists():
                    return FileResponse(p, media_type="text/html")
                return HTMLResponse("<h1>Page not found</h1>", status_code=404)
            return handler
        
        app.get(route, tags=["Frontend"])(_make_handler(filepath))
    
    return app
