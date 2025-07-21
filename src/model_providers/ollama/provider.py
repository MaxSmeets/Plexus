"""
Ollama model provider implementation for the Plexus agentic system.

This module provides integration with Ollama for running local LLMs,
implementing the BaseModelProvider interface for consistent usage.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Union, AsyncGenerator, Any
import aiohttp
from datetime import datetime

from ..base_provider import (
    BaseModelProvider, 
    ChatMessage, 
    ModelParameters, 
    ModelResponse, 
    StreamChunk,
    MessageRole
)


logger = logging.getLogger(__name__)


class OllamaProvider(BaseModelProvider):
    """
    Ollama model provider for local LLM inference.
    
    Provides integration with Ollama's REST API for running local language models.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Ollama provider.
        
        Args:
            config: Configuration dictionary with the following keys:
                - base_url (str): Ollama server URL (default: http://localhost:11434)
                - timeout (int): Request timeout in seconds (default: 300)
                - keep_alive (str): How long to keep models loaded (default: 5m)
        """
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.timeout = config.get("timeout", 300)
        self.keep_alive = config.get("keep_alive", "5m")
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self) -> bool:
        """
        Initialize the Ollama provider and check if it's available.
        
        Returns:
            bool: True if Ollama is available and responding
        """
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Test connection by listing models
            await self.list_models()
            self.is_available = True
            logger.info(f"Ollama provider initialized successfully at {self.base_url}")
            return True
            
        except Exception as e:
            self.is_available = False
            logger.error(f"Failed to initialize Ollama provider: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            return False
    
    async def list_models(self) -> List[str]:
        """
        List all available models in Ollama.
        
        Returns:
            List[str]: List of available model names
        """
        if not self.session:
            raise RuntimeError("Provider not initialized")
            
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    logger.debug(f"Found {len(models)} models in Ollama")
                    return models
                else:
                    error_msg = f"Failed to list models: HTTP {response.status}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
                    
        except aiohttp.ClientError as e:
            error_msg = f"Network error while listing models: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    async def generate_chat(
        self,
        messages: List[ChatMessage],
        model: str,
        parameters: Optional[ModelParameters] = None
    ) -> Union[ModelResponse, AsyncGenerator[StreamChunk, None]]:
        """
        Generate a chat completion using Ollama's chat API.
        
        Args:
            messages: List of chat messages
            model: Name of the model to use
            parameters: Optional parameters for generation
            
        Returns:
            Either a complete response or an async generator for streaming
        """
        if not self.session:
            raise RuntimeError("Provider not initialized")
        
        if not messages:
            raise ValueError("Messages list cannot be empty")
        
        params = parameters or ModelParameters()
        
        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            ollama_msg = {
                "role": msg.role.value,
                "content": msg.content
            }
            if msg.images:
                ollama_msg["images"] = msg.images
            if msg.tool_calls:
                ollama_msg["tool_calls"] = msg.tool_calls
            ollama_messages.append(ollama_msg)
        
        # Build request payload
        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": params.stream,
            "keep_alive": self.keep_alive
        }
        
        # Add optional parameters
        options = {}
        if params.temperature != 0.7:
            options["temperature"] = params.temperature
        if params.top_p != 0.9:
            options["top_p"] = params.top_p
        if params.top_k is not None:
            options["top_k"] = params.top_k
        if params.seed is not None:
            options["seed"] = params.seed
        if params.stop_sequences:
            options["stop"] = params.stop_sequences
        
        if params.extra_params:
            options.update(params.extra_params)
            
        if options:
            payload["options"] = options
        
        if params.stream:
            return self._stream_chat_response(payload)
        else:
            return await self._get_chat_response(payload)
    
    async def _get_chat_response(self, payload: Dict[str, Any]) -> ModelResponse:
        """Get a non-streaming chat response."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return ModelResponse(
                        content=data["message"]["content"],
                        model=data["model"],
                        role=MessageRole.ASSISTANT,
                        finish_reason=data.get("done_reason"),
                        token_usage={
                            "prompt_tokens": data.get("prompt_eval_count", 0),
                            "completion_tokens": data.get("eval_count", 0),
                            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                        },
                        metadata={
                            "created_at": data.get("created_at"),
                            "total_duration": data.get("total_duration"),
                            "load_duration": data.get("load_duration"),
                            "prompt_eval_duration": data.get("prompt_eval_duration"),
                            "eval_duration": data.get("eval_duration")
                        }
                    )
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Chat request failed: HTTP {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Network error during chat: {e}")
    
    async def _stream_chat_response(self, payload: Dict[str, Any]) -> AsyncGenerator[StreamChunk, None]:
        """Stream chat response chunks."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Stream chat request failed: HTTP {response.status} - {error_text}")
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            content = data.get("message", {}).get("content", "")
                            is_final = data.get("done", False)
                            
                            metadata = None
                            if is_final:
                                metadata = {
                                    "created_at": data.get("created_at"),
                                    "total_duration": data.get("total_duration"),
                                    "load_duration": data.get("load_duration"),
                                    "prompt_eval_count": data.get("prompt_eval_count"),
                                    "prompt_eval_duration": data.get("prompt_eval_duration"),
                                    "eval_count": data.get("eval_count"),
                                    "eval_duration": data.get("eval_duration")
                                }
                            
                            yield StreamChunk(
                                content=content,
                                is_final=is_final,
                                metadata=metadata
                            )
                            
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON line: {line}")
                            continue
                            
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Network error during streaming chat: {e}")
    
    async def generate_completion(
        self,
        prompt: str,
        model: str,
        parameters: Optional[ModelParameters] = None
    ) -> Union[ModelResponse, AsyncGenerator[StreamChunk, None]]:
        """
        Generate a text completion using Ollama's generate API.
        
        Args:
            prompt: Input prompt
            model: Name of the model to use
            parameters: Optional parameters for generation
            
        Returns:
            Either a complete response or an async generator for streaming
        """
        if not self.session:
            raise RuntimeError("Provider not initialized")
        
        if not prompt:
            raise ValueError("Prompt cannot be empty")
        
        params = parameters or ModelParameters()
        
        # Build request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": params.stream,
            "keep_alive": self.keep_alive
        }
        
        # Add optional parameters
        options = {}
        if params.temperature != 0.7:
            options["temperature"] = params.temperature
        if params.top_p != 0.9:
            options["top_p"] = params.top_p
        if params.top_k is not None:
            options["top_k"] = params.top_k
        if params.seed is not None:
            options["seed"] = params.seed
        if params.stop_sequences:
            options["stop"] = params.stop_sequences
        
        if params.extra_params:
            options.update(params.extra_params)
            
        if options:
            payload["options"] = options
        
        if params.stream:
            return self._stream_completion_response(payload)
        else:
            return await self._get_completion_response(payload)
    
    async def _get_completion_response(self, payload: Dict[str, Any]) -> ModelResponse:
        """Get a non-streaming completion response."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return ModelResponse(
                        content=data["response"],
                        model=data["model"],
                        role=MessageRole.ASSISTANT,
                        finish_reason=data.get("done_reason"),
                        token_usage={
                            "prompt_tokens": data.get("prompt_eval_count", 0),
                            "completion_tokens": data.get("eval_count", 0),
                            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                        },
                        metadata={
                            "created_at": data.get("created_at"),
                            "total_duration": data.get("total_duration"),
                            "load_duration": data.get("load_duration"),
                            "prompt_eval_duration": data.get("prompt_eval_duration"),
                            "eval_duration": data.get("eval_duration"),
                            "context": data.get("context")
                        }
                    )
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Generate request failed: HTTP {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Network error during completion: {e}")
    
    async def _stream_completion_response(self, payload: Dict[str, Any]) -> AsyncGenerator[StreamChunk, None]:
        """Stream completion response chunks."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Stream generate request failed: HTTP {response.status} - {error_text}")
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            content = data.get("response", "")
                            is_final = data.get("done", False)
                            
                            metadata = None
                            if is_final:
                                metadata = {
                                    "created_at": data.get("created_at"),
                                    "total_duration": data.get("total_duration"),
                                    "load_duration": data.get("load_duration"),
                                    "prompt_eval_count": data.get("prompt_eval_count"),
                                    "prompt_eval_duration": data.get("prompt_eval_duration"),
                                    "eval_count": data.get("eval_count"),
                                    "eval_duration": data.get("eval_duration"),
                                    "context": data.get("context")
                                }
                            
                            yield StreamChunk(
                                content=content,
                                is_final=is_final,
                                metadata=metadata
                            )
                            
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON line: {line}")
                            continue
                            
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Network error during streaming completion: {e}")
    
    async def generate_embeddings(
        self,
        texts: List[str],
        model: str
    ) -> List[List[float]]:
        """
        Generate embeddings for the given texts using Ollama.
        
        Args:
            texts: List of texts to generate embeddings for
            model: Name of the embedding model to use
            
        Returns:
            List of embedding vectors
        """
        if not self.session:
            raise RuntimeError("Provider not initialized")
        
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        try:
            # Ollama's embed API supports multiple inputs
            payload = {
                "model": model,
                "input": texts,
                "keep_alive": self.keep_alive
            }
            
            async with self.session.post(
                f"{self.base_url}/api/embed",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    embeddings = data.get("embeddings", [])
                    
                    if len(embeddings) != len(texts):
                        raise RuntimeError(f"Expected {len(texts)} embeddings, got {len(embeddings)}")
                    
                    return embeddings
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Embedding request failed: HTTP {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Network error during embedding generation: {e}")
    
    async def pull_model(self, model: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Pull (download) a model from the Ollama library.
        
        Args:
            model: Name of the model to pull
            
        Yields:
            Progress updates during the download
        """
        if not self.session:
            raise RuntimeError("Provider not initialized")
        
        try:
            payload = {"model": model}
            
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Pull request failed: HTTP {response.status} - {error_text}")
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            yield data
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON line: {line}")
                            continue
                            
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Network error during model pull: {e}")
    
    async def delete_model(self, model: str) -> bool:
        """
        Delete a model from Ollama.
        
        Args:
            model: Name of the model to delete
            
        Returns:
            bool: True if deletion was successful
        """
        if not self.session:
            raise RuntimeError("Provider not initialized")
        
        try:
            payload = {"model": model}
            
            async with self.session.delete(
                f"{self.base_url}/api/delete",
                json=payload
            ) as response:
                return response.status == 200
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error during model deletion: {e}")
            return False
    
    async def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get detailed information about a model.
        
        Args:
            model: Name of the model
            
        Returns:
            Dict containing model information
        """
        if not self.session:
            raise RuntimeError("Provider not initialized")
        
        try:
            payload = {"model": model}
            
            async with self.session.post(
                f"{self.base_url}/api/show",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Show model request failed: HTTP {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Network error during model info retrieval: {e}")
    
    async def list_running_models(self) -> List[Dict[str, Any]]:
        """
        List models currently loaded in memory.
        
        Returns:
            List of running model information
        """
        if not self.session:
            raise RuntimeError("Provider not initialized")
        
        try:
            async with self.session.get(f"{self.base_url}/api/ps") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"List running models request failed: HTTP {response.status} - {error_text}")
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Network error during running models listing: {e}")
    
    async def close(self):
        """Close the HTTP session and clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_available = False
    
    def __del__(self):
        """Cleanup when the object is garbage collected."""
        if self.session and not self.session.closed:
            # Schedule the cleanup for the next event loop iteration
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except RuntimeError:
                # Event loop is not running, can't clean up properly
                pass
