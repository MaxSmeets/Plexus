"""
Health check routes for the Plexus API.
"""

import time
from fastapi import APIRouter, Request
from ..schemas import HealthResponse, SuccessResponse
from ...core import settings, create_response_envelope

router = APIRouter(prefix="/health", tags=["health"])

# Track service start time
service_start_time = time.time()


@router.get(
    "",
    response_model=SuccessResponse,
    summary="Health Check",
    description="Check the health status of the API service"
)
async def health_check(request: Request) -> SuccessResponse:
    """
    Perform a health check on the API service.
    
    Returns the service status, version, current timestamp, and uptime.
    """
    current_time = time.time()
    uptime = current_time - service_start_time
    
    health_data = HealthResponse(
        status="healthy",
        version=settings.VERSION,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(current_time)),
        uptime=uptime
    )
    
    return create_response_envelope(
        data=health_data.dict(),
        message="Service is healthy",
        request_id=getattr(request.state, 'request_id', None)
    )


@router.get(
    "/ready",
    response_model=SuccessResponse,
    summary="Readiness Check",
    description="Check if the API is ready to serve requests"
)
async def readiness_check(request: Request) -> SuccessResponse:
    """
    Check if the API is ready to serve requests.
    
    This endpoint can be used by load balancers and orchestrators
    to determine if the service is ready to handle traffic.
    """
    # Here you could add checks for database connectivity,
    # external service availability, etc.
    
    return create_response_envelope(
        data={"ready": True},
        message="Service is ready",
        request_id=getattr(request.state, 'request_id', None)
    )


@router.get(
    "/live",
    response_model=SuccessResponse,
    summary="Liveness Check",
    description="Check if the API service is alive"
)
async def liveness_check(request: Request) -> SuccessResponse:
    """
    Check if the API service is alive.
    
    This endpoint can be used by orchestrators to determine
    if the service should be restarted.
    """
    return create_response_envelope(
        data={"alive": True},
        message="Service is alive",
        request_id=getattr(request.state, 'request_id', None)
    )
