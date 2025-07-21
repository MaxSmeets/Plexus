"""
Utility functions for the Ollama model provider.

This module provides helper functions for working with Ollama,
including model management, response parsing, and error handling.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import re


logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Base exception for Ollama-related errors."""
    pass


class ModelNotFoundError(OllamaError):
    """Raised when a requested model is not available."""
    pass


class ConnectionError(OllamaError):
    """Raised when unable to connect to Ollama server."""
    pass


class ResponseParsingError(OllamaError):
    """Raised when unable to parse Ollama response."""
    pass


def parse_model_name(model_name: str) -> Tuple[str, str]:
    """
    Parse a model name into base name and tag.
    
    Args:
        model_name: Model name in format "name:tag" or just "name"
        
    Returns:
        Tuple of (base_name, tag)
    """
    if ":" in model_name:
        base_name, tag = model_name.split(":", 1)
    else:
        base_name, tag = model_name, "latest"
    
    return base_name, tag


def format_model_name(base_name: str, tag: str = "latest") -> str:
    """
    Format a model name from base name and tag.
    
    Args:
        base_name: Base model name
        tag: Model tag (default: "latest")
        
    Returns:
        Formatted model name
    """
    return f"{base_name}:{tag}"


def validate_model_name(model_name: str) -> bool:
    """
    Validate a model name format.
    
    Args:
        model_name: Model name to validate
        
    Returns:
        bool: True if valid
    """
    # Basic validation - alphanumeric, hyphens, underscores, dots, colons
    pattern = r'^[a-zA-Z0-9._-]+(?::[a-zA-Z0-9._-]+)?$'
    return bool(re.match(pattern, model_name))


def calculate_tokens_per_second(eval_count: int, eval_duration: int) -> float:
    """
    Calculate tokens per second from Ollama metrics.
    
    Args:
        eval_count: Number of tokens generated
        eval_duration: Duration in nanoseconds
        
    Returns:
        Tokens per second
    """
    if eval_duration <= 0:
        return 0.0
    
    # Convert nanoseconds to seconds
    duration_seconds = eval_duration / 1_000_000_000
    return eval_count / duration_seconds


def format_duration(nanoseconds: int) -> str:
    """
    Format duration from nanoseconds to human-readable string.
    
    Args:
        nanoseconds: Duration in nanoseconds
        
    Returns:
        Formatted duration string
    """
    if nanoseconds < 1_000:
        return f"{nanoseconds}ns"
    elif nanoseconds < 1_000_000:
        return f"{nanoseconds / 1_000:.1f}μs"
    elif nanoseconds < 1_000_000_000:
        return f"{nanoseconds / 1_000_000:.1f}ms"
    else:
        return f"{nanoseconds / 1_000_000_000:.2f}s"


def parse_keep_alive(keep_alive: str) -> timedelta:
    """
    Parse keep_alive string to timedelta.
    
    Args:
        keep_alive: Keep alive string (e.g., "5m", "1h", "30s")
        
    Returns:
        timedelta object
    """
    if not keep_alive:
        return timedelta(minutes=5)  # Default
    
    # Parse time units
    pattern = r'^(\d+)([smhd])$'
    match = re.match(pattern, keep_alive.lower())
    
    if not match:
        raise ValueError(f"Invalid keep_alive format: {keep_alive}")
    
    value, unit = match.groups()
    value = int(value)
    
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    else:
        raise ValueError(f"Invalid time unit: {unit}")


def format_model_size(size_bytes: int) -> str:
    """
    Format model size in bytes to human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def extract_model_info(model_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract useful information from Ollama model data.
    
    Args:
        model_data: Raw model data from Ollama API
        
    Returns:
        Extracted model information
    """
    details = model_data.get("details", {})
    
    return {
        "name": model_data.get("name", ""),
        "size": model_data.get("size", 0),
        "size_formatted": format_model_size(model_data.get("size", 0)),
        "modified_at": model_data.get("modified_at", ""),
        "digest": model_data.get("digest", ""),
        "format": details.get("format", ""),
        "family": details.get("family", ""),
        "families": details.get("families", []),
        "parameter_size": details.get("parameter_size", ""),
        "quantization_level": details.get("quantization_level", "")
    }


def is_embedding_model(model_name: str) -> bool:
    """
    Check if a model is likely an embedding model based on its name.
    
    Args:
        model_name: Name of the model
        
    Returns:
        bool: True if likely an embedding model
    """
    embedding_keywords = [
        "embed", "embedding", "sentence", "all-minilm", "bge", "e5",
        "instructor", "gte", "multilingual-e5"
    ]
    
    model_lower = model_name.lower()
    return any(keyword in model_lower for keyword in embedding_keywords)


def is_multimodal_model(model_name: str) -> bool:
    """
    Check if a model supports multimodal input (text + images).
    
    Args:
        model_name: Name of the model
        
    Returns:
        bool: True if likely a multimodal model
    """
    multimodal_keywords = ["llava", "bakllava", "moondream", "vision"]
    
    model_lower = model_name.lower()
    return any(keyword in model_lower for keyword in multimodal_keywords)


def estimate_memory_usage(parameter_size: str, quantization: str = "") -> Optional[int]:
    """
    Estimate memory usage for a model based on parameter size and quantization.
    
    Args:
        parameter_size: Parameter size string (e.g., "7B", "13B")
        quantization: Quantization level (e.g., "Q4_0", "Q8_0")
        
    Returns:
        Estimated memory usage in bytes, or None if cannot estimate
    """
    # Extract parameter count
    size_match = re.match(r'(\d+(?:\.\d+)?)([BMK])', parameter_size.upper())
    if not size_match:
        return None
    
    value, unit = size_match.groups()
    value = float(value)
    
    # Convert to number of parameters
    if unit == 'B':
        params = value * 1_000_000_000
    elif unit == 'M':
        params = value * 1_000_000
    elif unit == 'K':
        params = value * 1_000
    else:
        return None
    
    # Estimate bytes per parameter based on quantization
    if "Q2" in quantization:
        bytes_per_param = 0.25
    elif "Q3" in quantization:
        bytes_per_param = 0.375
    elif "Q4" in quantization:
        bytes_per_param = 0.5
    elif "Q5" in quantization:
        bytes_per_param = 0.625
    elif "Q6" in quantization:
        bytes_per_param = 0.75
    elif "Q8" in quantization:
        bytes_per_param = 1.0
    else:
        # Assume FP16 for unknown quantization
        bytes_per_param = 2.0
    
    # Add overhead for KV cache and other memory usage (rough estimate)
    overhead_factor = 1.2
    
    return int(params * bytes_per_param * overhead_factor)


async def retry_with_exponential_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple = (Exception,)
):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Result of the function call
        
    Raises:
        The last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                break
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {e}")
            await asyncio.sleep(delay)
    
    raise last_exception


def sanitize_model_response(response: str) -> str:
    """
    Sanitize model response by removing potentially harmful content.
    
    Args:
        response: Raw model response
        
    Returns:
        Sanitized response
    """
    # Remove null bytes and other control characters
    sanitized = response.replace('\x00', '').replace('\x08', '')
    
    # Normalize whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def chunk_text_for_embeddings(
    text: str,
    max_chunk_size: int = 512,
    overlap: int = 50
) -> List[str]:
    """
    Split text into chunks suitable for embedding generation.
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            sentence_end = text.rfind('.', start, end)
            if sentence_end > start + max_chunk_size // 2:
                end = sentence_end + 1
            else:
                # Look for word boundary
                word_boundary = text.rfind(' ', start, end)
                if word_boundary > start + max_chunk_size // 2:
                    end = word_boundary
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = max(start + 1, end - overlap)
    
    return chunks
