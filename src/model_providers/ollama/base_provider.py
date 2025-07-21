"""Base provider classes and data models for Ollama."""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass


class MessageRole(str, Enum):
    """Message roles for chat conversations."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: MessageRole
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class ModelParameters:
    """Parameters for model inference."""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stream: Optional[bool] = None
    
    def __post_init__(self):
        """Validate parameters."""
        if self.temperature is not None:
            if not (0.0 <= self.temperature <= 2.0):
                raise ValueError("Temperature must be between 0.0 and 2.0")
        
        if self.max_tokens is not None:
            if self.max_tokens <= 0:
                raise ValueError("max_tokens must be positive")
    
    def to_ollama_options(self) -> Dict[str, Any]:
        """Convert to Ollama API options format."""
        options = {}
        
        if self.temperature is not None:
            options["temperature"] = self.temperature
        if self.max_tokens is not None:
            options["num_predict"] = self.max_tokens  # Ollama uses num_predict
        if self.top_p is not None:
            options["top_p"] = self.top_p
        if self.top_k is not None:
            options["top_k"] = self.top_k
            
        return options
