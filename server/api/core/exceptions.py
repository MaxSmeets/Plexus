"""
Core exceptions for the Plexus API.
"""

from typing import Any, Dict, Optional


class PlexusAPIException(Exception):
    """Base exception for Plexus API."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(PlexusAPIException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, details=details)


class NotFoundError(PlexusAPIException):
    """Raised when a resource is not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class UnauthorizedError(PlexusAPIException):
    """Raised when authentication is required."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401)


class ForbiddenError(PlexusAPIException):
    """Raised when access is forbidden."""
    
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, status_code=403)


class RateLimitError(PlexusAPIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)
