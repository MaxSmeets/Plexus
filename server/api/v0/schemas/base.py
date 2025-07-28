"""
Base schemas for the Plexus API.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    timestamp: str = Field(..., description="Response timestamp in ISO format")
    request_id: Optional[str] = Field(None, description="Unique request identifier")


class SuccessResponse(BaseResponse):
    """Success response model."""
    
    data: Optional[Any] = Field(None, description="Response data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"key": "value"},
                "timestamp": "2025-07-28T10:00:00Z",
                "request_id": "uuid-string"
            }
        }


class ErrorResponse(BaseResponse):
    """Error response model."""
    
    error: dict = Field(..., description="Error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "An error occurred",
                "error": {
                    "code": 400,
                    "details": {"field": "error description"}
                },
                "timestamp": "2025-07-28T10:00:00Z",
                "request_id": "uuid-string"
            }
        }


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Health check timestamp")
    uptime: float = Field(..., description="Service uptime in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "timestamp": "2025-07-28T10:00:00Z",
                "uptime": 3600.0
            }
        }
