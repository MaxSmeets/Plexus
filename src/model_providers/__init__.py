"""
Model Providers package for the Plexus agentic system.

This package contains integrations with various LLM providers and local model runners,
providing a unified interface for text generation, chat, and embeddings.
"""

from .base_provider import (
    BaseModelProvider,
    ChatMessage,
    ModelParameters,
    ModelResponse,
    StreamChunk,
    MessageRole
)

# Import available providers
try:
    from .ollama import OllamaProvider, OllamaConfig
    _OLLAMA_AVAILABLE = True
except ImportError:
    _OLLAMA_AVAILABLE = False

__version__ = "1.0.0"
__author__ = "Plexus Team"

# Available providers registry
AVAILABLE_PROVIDERS = {}

if _OLLAMA_AVAILABLE:
    AVAILABLE_PROVIDERS["ollama"] = OllamaProvider

__all__ = [
    # Base classes
    "BaseModelProvider",
    "ChatMessage", 
    "ModelParameters",
    "ModelResponse",
    "StreamChunk",
    "MessageRole",
    
    # Provider registry
    "AVAILABLE_PROVIDERS",
]

# Add provider-specific exports if available
if _OLLAMA_AVAILABLE:
    __all__.extend(["OllamaProvider", "OllamaConfig"])


def get_available_providers():
    """
    Get list of available provider names.
    
    Returns:
        List[str]: Names of available providers
    """
    return list(AVAILABLE_PROVIDERS.keys())


def create_provider(provider_name: str, config: dict):
    """
    Create a provider instance by name.
    
    Args:
        provider_name: Name of the provider (e.g., "ollama")
        config: Configuration dictionary for the provider
        
    Returns:
        BaseModelProvider: Provider instance
        
    Raises:
        ValueError: If provider is not available
    """
    if provider_name not in AVAILABLE_PROVIDERS:
        available = ", ".join(get_available_providers())
        raise ValueError(f"Provider '{provider_name}' not available. Available: {available}")
    
    provider_class = AVAILABLE_PROVIDERS[provider_name]
    return provider_class(config)
