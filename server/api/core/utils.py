"""
Core utilities for the Plexus API.
"""

import time
from typing import Any, Dict
from datetime import datetime
import uuid


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


def create_response_envelope(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
    request_id: str = None
) -> Dict[str, Any]:
    """Create a standardized response envelope."""
    return {
        "success": 200 <= status_code < 400,
        "message": message,
        "data": data,
        "timestamp": get_current_timestamp(),
        "request_id": request_id
    }


def create_error_response(
    message: str,
    status_code: int = 500,
    details: Dict[str, Any] = None,
    request_id: str = None
) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "success": False,
        "message": message,
        "error": {
            "code": status_code,
            "details": details or {}
        },
        "timestamp": get_current_timestamp(),
        "request_id": request_id
    }
