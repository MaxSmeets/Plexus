"""
CORS middleware configuration for the Plexus API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..core.config import settings


def add_cors_middleware(app: FastAPI) -> None:
    """Add CORS middleware to the FastAPI app."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )
