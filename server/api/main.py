"""
Main FastAPI application for the Plexus API.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse

from .core import settings, PlexusAPIException, create_error_response
from .middleware import add_cors_middleware, LoggingMiddleware, RateLimitMiddleware
from .v0 import health_router, agents_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Plexus API...")
    logger.info(f"API Version: {settings.VERSION}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Plexus API...")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V0_STR}/openapi.json",
        docs_url=f"{settings.API_V0_STR}/docs",
        redoc_url=f"{settings.API_V0_STR}/redoc",
        lifespan=lifespan
    )
    
    # Add middleware
    add_cors_middleware(app)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    # Add route handlers
    app.include_router(health_router, prefix=settings.API_V0_STR)
    app.include_router(agents_router, prefix=settings.API_V0_STR)
    
    # Exception handlers
    @app.exception_handler(PlexusAPIException)
    async def plexus_exception_handler(request: Request, exc: PlexusAPIException):
        """Handle custom Plexus API exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                message=exc.message,
                status_code=exc.status_code,
                details=exc.details,
                request_id=getattr(request.state, 'request_id', None)
            )
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler_override(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with consistent format."""
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                message=exc.detail,
                status_code=exc.status_code,
                request_id=getattr(request.state, 'request_id', None)  
            )
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                message="Internal server error",
                status_code=500,
                details={"error": str(exc) if settings.DEBUG else "Internal server error"},
                request_id=getattr(request.state, 'request_id', None)
            )
        )
    
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint redirect to docs."""
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": settings.VERSION,
            "docs": f"{settings.API_V0_STR}/docs",
            "health": f"{settings.API_V0_STR}/health"
        }
    
    return app


# Create the app instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level="info" if settings.DEBUG else "warning"
    )
