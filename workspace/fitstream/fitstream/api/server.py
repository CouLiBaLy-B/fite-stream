"""
FitStream API Server
Entry point for the API — uses the application factory.

Run with:
    python -m fitstream.api.server
    # or
    uvicorn fitstream.api.server:app --host 0.0.0.0 --port 8000

The actual app creation and routing is in app_factory.py.
This file just creates the app instance and provides the CLI entry point.
"""

from fitstream.api.app_factory import create_app

# Create the app instance (used by uvicorn)
app = create_app()


if __name__ == "__main__":
    import uvicorn
    from loguru import logger
    from fitstream import __version__
    from fitstream.config import get_config
    
    config = get_config()
    
    logger.info(f"🎬 Starting FitStream API v{__version__}")
    
    uvicorn.run(
        "fitstream.api.server:app",
        host=config.api.host,
        port=config.api.port,
        reload=False,
        log_level="info",
    )
