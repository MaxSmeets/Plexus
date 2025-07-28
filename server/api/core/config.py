"""
Core configuration settings for the Plexus API.
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Info
    API_V0_STR: str = "/api/v0"
    PROJECT_NAME: str = "Plexus API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "A modern API for the Plexus application"
    
    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    RELOAD: bool = True
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:8000",  # API server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5500"   # Live server for quick testing
    ]
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    # Agent Configuration
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # Allow extra fields to prevent validation errors
    }


settings = Settings()
