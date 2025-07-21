"""
Ollama model provider package for the Plexus agentic system.

This package provides integration with Ollama for running local language models,
including chat completions, text generation, and embeddings.
"""

from .provider import OllamaProvider
from .config import OllamaConfig, get_default_config, load_config
from .utils import (
    OllamaError,
    ModelNotFoundError,
    ConnectionError,
    ResponseParsingError,
    parse_model_name,
    format_model_name,
    validate_model_name,
    calculate_tokens_per_second,
    format_duration,
    format_model_size,
    extract_model_info,
    is_embedding_model,
    is_multimodal_model,
    estimate_memory_usage,
    sanitize_model_response,
    chunk_text_for_embeddings
)

__version__ = "1.0.0"
__author__ = "Plexus Team"

__all__ = [
    # Main classes
    "OllamaProvider",
    "OllamaConfig",
    
    # Configuration functions
    "get_default_config",
    "load_config",
    
    # Exceptions
    "OllamaError",
    "ModelNotFoundError",
    "ConnectionError",
    "ResponseParsingError",
    
    # Utility functions
    "parse_model_name",
    "format_model_name",
    "validate_model_name",
    "calculate_tokens_per_second",
    "format_duration",
    "format_model_size",
    "extract_model_info",
    "is_embedding_model",
    "is_multimodal_model",
    "estimate_memory_usage",
    "sanitize_model_response",
    "chunk_text_for_embeddings"
]
