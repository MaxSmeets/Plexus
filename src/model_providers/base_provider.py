"""
Base model provider interface for the Plexus agentic system.

This module defines the abstract base class that all model providers must implement,
ensuring consistent interfaces across different LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, AsyncGenerator, Any
from dataclasses import dataclass
from enum import Enum
import asyncio


class MessageRole(Enum):
    """Enum for message roles in chat conversations."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ChatMessage:
    """Represents a single message in a chat conversation."""
    role: MessageRole
    content: str
    images: Optional[List[str]] = None  # Base64 encoded images for multimodal models
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class ModelParameters:
    """Configuration parameters for model inference."""
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    stream: bool = True
    stop_sequences: Optional[List[str]] = None
    seed: Optional[int] = None
    
    # Additional provider-specific parameters
    extra_params: Optional[Dict[str, Any]] = None


@dataclass
class ModelResponse:
    """Response from a model provider."""
    content: str
    model: str
    role: MessageRole = MessageRole.ASSISTANT
    finish_reason: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StreamChunk:
    """A single chunk in a streaming response."""
    content: str
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = None


class BaseModelProvider(ABC):
    """
    Abstract base class for all model providers.
    
    This class defines the interface that all model providers must implement
    to ensure consistency across different LLM providers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the model provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.is_available = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the provider and check if it's available.
        
        Returns:
            bool: True if the provider is successfully initialized and available
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """
        List all available models for this provider.
        
        Returns:
            List[str]: List of available model names
        """
        pass
    
    @abstractmethod
    async def generate_chat(
        self,
        messages: List[ChatMessage],
        model: str,
        parameters: Optional[ModelParameters] = None
    ) -> Union[ModelResponse, AsyncGenerator[StreamChunk, None]]:
        """
        Generate a chat completion.
        
        Args:
            messages: List of chat messages
            model: Name of the model to use
            parameters: Optional parameters for generation
            
        Returns:
            Either a complete response or an async generator for streaming
        """
        pass
    
    @abstractmethod
    async def generate_completion(
        self,
        prompt: str,
        model: str,
        parameters: Optional[ModelParameters] = None
    ) -> Union[ModelResponse, AsyncGenerator[StreamChunk, None]]:
        """
        Generate a text completion.
        
        Args:
            prompt: Input prompt
            model: Name of the model to use
            parameters: Optional parameters for generation
            
        Returns:
            Either a complete response or an async generator for streaming
        """
        pass
    
    @abstractmethod
    async def generate_embeddings(
        self,
        texts: List[str],
        model: str
    ) -> List[List[float]]:
        """
        Generate embeddings for the given texts.
        
        Args:
            texts: List of texts to generate embeddings for
            model: Name of the embedding model to use
            
        Returns:
            List of embedding vectors
        """
        pass
    
    async def is_model_available(self, model: str) -> bool:
        """
        Check if a specific model is available.
        
        Args:
            model: Name of the model to check
            
        Returns:
            bool: True if the model is available
        """
        try:
            available_models = await self.list_models()
            return model in available_models
        except Exception:
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the provider.
        
        Returns:
            Dict containing health status information
        """
        try:
            models = await self.list_models()
            return {
                "status": "healthy",
                "available": self.is_available,
                "models_count": len(models),
                "provider": self.__class__.__name__
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "available": False,
                "error": str(e),
                "provider": self.__class__.__name__
            }
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about this provider.
        
        Returns:
            Dict containing provider information
        """
        return {
            "name": self.__class__.__name__,
            "config": self.config,
            "available": self.is_available
        }
