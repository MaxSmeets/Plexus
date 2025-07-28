# Plexus API

A modern, scalable REST API for the Plexus application built with FastAPI following industry best practices.

## Features

- **FastAPI Framework**: High-performance async API framework with automatic OpenAPI documentation
- **Modern Architecture**: Clean separation of concerns with middleware, routes, schemas, and core utilities
- **API Versioning**: Proper versioning strategy starting with v0
- **Request/Response Logging**: Comprehensive logging with unique request IDs
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **CORS Support**: Configurable CORS for frontend integration
- **Error Handling**: Standardized error responses with proper HTTP status codes
- **Health Checks**: Multiple health check endpoints for monitoring
- **Auto Documentation**: Interactive API documentation with Swagger UI and ReDoc

## Project Structure

```
server/api/
├── core/                    # Core functionality
│   ├── __init__.py         
│   ├── config.py           # Application configuration
│   ├── exceptions.py       # Custom exceptions
│   └── utils.py            # Utility functions
├── middleware/             # Custom middleware
│   ├── __init__.py
│   ├── cors.py            # CORS configuration
│   ├── logging.py         # Request/response logging
│   └── rate_limit.py      # Rate limiting
├── v0/                     # API version 0
│   ├── __init__.py
│   ├── routes/            # Route handlers
│   │   ├── __init__.py
│   │   ├── health.py      # Health check endpoints
│   │   └── agents.py      # Agent interaction endpoints
│   └── schemas/           # Pydantic models
│       ├── __init__.py
│       ├── base.py        # Base response models
│       └── agents.py      # Agent-specific models
├── main.py                # Main FastAPI application
├── run_dev.py            # Development server script
├── .env.example          # Environment variables template
└── api.md                # This documentation
```

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp server/api/.env.example server/api/.env
   # Edit .env file with your configuration
   ```

## Running the API

### Development Server

```bash
# Option 1: Using the development script
python server/api/run_dev.py

# Option 2: Using uvicorn directly
uvicorn server.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Production Server

```bash
# Using gunicorn (recommended for production)
gunicorn server.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Endpoints

### Base URL
- Development: `http://localhost:8000`
- API Base Path: `/api/v0`

### Documentation
- **Swagger UI**: `http://localhost:8000/api/v0/docs`
- **ReDoc**: `http://localhost:8000/api/v0/redoc`
- **OpenAPI Schema**: `http://localhost:8000/api/v0/openapi.json`

### Health Endpoints
- `GET /api/v0/health` - Basic health check
- `GET /api/v0/health/ready` - Readiness probe
- `GET /api/v0/health/live` - Liveness probe

### Agent Endpoints
- `POST /api/v0/agents/shopping-list` - Interact with shopping list agent
- `GET /api/v0/agents/available` - List available agents

## Response Format

All API responses follow a standardized format:

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "timestamp": "2025-07-28T10:00:00Z",
  "request_id": "uuid-string"
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description",
  "error": {
    "code": 400,
    "details": { ... }
  },
  "timestamp": "2025-07-28T10:00:00Z",
  "request_id": "uuid-string"
}
```

## Configuration

The API uses environment variables for configuration. Key settings include:

- `SECRET_KEY`: Secret key for security (change in production)
- `DEBUG`: Enable debug mode (default: true)
- `HOST`: Server host (default: 127.0.0.1)
- `PORT`: Server port (default: 8000)
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: Rate limit per client (default: 60)

## Middleware Stack

1. **CORS Middleware**: Handles cross-origin requests
2. **Logging Middleware**: Logs all requests/responses with unique IDs
3. **Rate Limiting Middleware**: Prevents API abuse

## Security Features

- Request rate limiting
- CORS protection
- Standardized error handling
- Request ID tracking
- Environment-based configuration

## Development Guidelines

### Adding New Endpoints

1. Create route handler in `v0/routes/`
2. Define Pydantic schemas in `v0/schemas/`
3. Add route to main application in `main.py`
4. Update documentation

### Error Handling

Use custom exceptions from `core.exceptions`:
- `ValidationError`: Input validation failures
- `NotFoundError`: Resource not found
- `UnauthorizedError`: Authentication required
- `ForbiddenError`: Access denied
- `RateLimitError`: Rate limit exceeded

### Testing

The API includes built-in testing capabilities:
- Interactive documentation for manual testing
- Health check endpoints for monitoring
- Detailed logging for debugging

## Monitoring

The API provides several monitoring capabilities:

- **Health Checks**: Multiple endpoints for different health aspects
- **Request Logging**: All requests logged with unique IDs
- **Performance Metrics**: Request processing time in headers
- **Error Tracking**: Comprehensive error logging

## Next Steps

1. Add authentication and authorization
2. Implement database integration
3. Add more comprehensive testing
4. Set up CI/CD pipeline
5. Add metrics and monitoring
6. Implement caching strategies