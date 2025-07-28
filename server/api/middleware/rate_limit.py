"""
Rate limiting middleware for the Plexus API.
"""

import time
from typing import Dict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self.client_requests: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        if client_ip in self.client_requests:
            self.client_requests[client_ip] = [
                req_time for req_time in self.client_requests[client_ip]
                if current_time - req_time < 60
            ]
        else:
            self.client_requests[client_ip] = []
        
        # Check rate limit
        if len(self.client_requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute."
            )
        
        # Add current request
        self.client_requests[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        return response
