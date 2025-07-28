"""
Routes package for the Plexus API v0.
"""

from .health import router as health_router
from .agents import router as agents_router

__all__ = [
    "health_router",
    "agents_router"
]
