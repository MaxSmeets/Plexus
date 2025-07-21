"""
Configuration utilities for the Ollama model provider.

This module provides configuration management and validation for Ollama settings.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import os


@dataclass
class OllamaConfig:
    """Configuration for the Ollama provider."""
    base_url: str = "http://localhost:11434"
    timeout: int = 300
    keep_alive: str = "5m"
    
    # Connection settings
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Default model parameters
    default_temperature: float = 0.7
    default_top_p: float = 0.9
    default_stream: bool = True
    
    # Additional settings
    verify_ssl: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls) -> 'OllamaConfig':
        """
        Create configuration from environment variables.
        
        Environment variables:
        - OLLAMA_BASE_URL: Base URL for Ollama server
        - OLLAMA_TIMEOUT: Request timeout in seconds
        - OLLAMA_KEEP_ALIVE: How long to keep models loaded
        - OLLAMA_MAX_RETRIES: Maximum number of retries
        - OLLAMA_RETRY_DELAY: Delay between retries
        - OLLAMA_VERIFY_SSL: Whether to verify SSL certificates
        
        Returns:
            OllamaConfig: Configuration instance
        """
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            timeout=int(os.getenv("OLLAMA_TIMEOUT", "300")),
            keep_alive=os.getenv("OLLAMA_KEEP_ALIVE", "5m"),
            max_retries=int(os.getenv("OLLAMA_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("OLLAMA_RETRY_DELAY", "1.0")),
            verify_ssl=os.getenv("OLLAMA_VERIFY_SSL", "true").lower() == "true"
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'OllamaConfig':
        """
        Create configuration from a dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            OllamaConfig: Configuration instance
        """
        return cls(**{k: v for k, v in config_dict.items() if hasattr(cls, k)})
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict containing configuration values
        """
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "keep_alive": self.keep_alive,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "default_temperature": self.default_temperature,
            "default_top_p": self.default_top_p,
            "default_stream": self.default_stream,
            "verify_ssl": self.verify_ssl,
            "custom_headers": self.custom_headers
        }
    
    def validate(self) -> bool:
        """
        Validate the configuration.
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.base_url:
            raise ValueError("base_url cannot be empty")
        
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        
        if self.retry_delay < 0:
            raise ValueError("retry_delay cannot be negative")
        
        if not (0.0 <= self.default_temperature <= 2.0):
            raise ValueError("default_temperature must be between 0.0 and 2.0")
        
        if not (0.0 <= self.default_top_p <= 1.0):
            raise ValueError("default_top_p must be between 0.0 and 1.0")
        
        return True


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration for Ollama provider.
    
    Returns:
        Dict containing default configuration
    """
    config = OllamaConfig()
    return config.to_dict()


def load_config(config_path: Optional[str] = None) -> OllamaConfig:
    """
    Load configuration from various sources.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        OllamaConfig: Loaded configuration
    """
    # Start with environment variables
    config = OllamaConfig.from_env()
    
    # If config file is provided, load and merge
    if config_path and os.path.exists(config_path):
        try:
            import json
            with open(config_path, 'r') as f:
                file_config = json.load(f)
            
            # Merge file config with env config
            for key, value in file_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                    
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"Failed to load config file {config_path}: {e}")
    
    # Validate the final configuration
    config.validate()
    
    return config
