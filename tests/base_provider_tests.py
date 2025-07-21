"""
Base test classes for model provider testing.

This module provides base test classes that can be inherited to create
consistent, comprehensive tests for any model provider.
"""
import pytest
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator, Type
from unittest.mock import AsyncMock

from tests.utils import (
    TestDataGenerator,
    PerformanceTracker,
    assert_valid_chat_response,
    assert_valid_embeddings_response,
    assert_valid_models_response,
    collect_stream,
)


class BaseProviderTest(ABC):
    """
    Base class for all model provider tests.
    
    This class provides common test patterns that should work
    for any model provider implementation.
    """
    
    # ========================================================================
    # Abstract methods - must be implemented by subclasses
    # ========================================================================
    
    @abstractmethod
    def provider_class(self) -> Type:
        """Return the provider class to test."""
        pass
    
    @abstractmethod
    def provider_config(self) -> Dict[str, Any]:
        """Return test configuration for the provider."""
        pass
    
    @abstractmethod
    def expected_models(self) -> List[str]:
        """Return list of models expected to be available."""
        pass
    
    @abstractmethod
    def test_model_name(self) -> str:
        """Return name of model to use for testing."""
        pass
    
    # ========================================================================
    # Provider lifecycle tests
    # ========================================================================
    
    @pytest.mark.unit
    def test_provider_initialization(self):
        """Test provider can be initialized with valid config."""
        provider_cls = self.provider_class()
        config = self.provider_config()
        
        provider = provider_cls(config)
        assert provider is not None
        
    @pytest.mark.unit
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_provider_session_management(self):
        """Test provider properly manages HTTP sessions."""
        provider_cls = self.provider_class()
        config = self.provider_config()
        provider = provider_cls(config)
        
        # Session should be None initially
        assert provider._session is None
        
        # Create session
        await provider._create_session()
        assert provider._session is not None
        
        # Close session
        await provider.close()
        assert provider._session.closed
    
    # ========================================================================
    # Configuration tests
    # ========================================================================
    
    @pytest.mark.unit
    def test_config_validation(self):
        """Test configuration validation."""
        provider_cls = self.provider_class()
        
        # Valid config should work
        valid_config = self.provider_config()
        provider = provider_cls(valid_config)
        assert provider.config is not None
        
    @pytest.mark.unit
    def test_config_defaults(self):
        """Test configuration defaults are properly set."""
        provider_cls = self.provider_class()
        config = self.provider_config()
        provider = provider_cls(config)
        
        # Common defaults that should exist
        assert hasattr(provider.config, 'timeout')
        assert hasattr(provider.config, 'max_retries')
        assert provider.config.timeout > 0
        assert provider.config.max_retries >= 0
    
    # ========================================================================
    # Mock-based unit tests
    # ========================================================================
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_chat_completion_unit(self):
        """Test chat completion with mocked responses."""
        provider = self._create_mock_provider({
            "message": {"content": "Mock response"},
            "done": True,
            "usage": {"eval_count": 10}
        })
        
        messages = TestDataGenerator.chat_messages(2)
        result = await provider.chat_completion(self.test_model_name(), messages)
        
        assert_valid_chat_response(result)
        assert "Mock response" in result["response"]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_text_generation_unit(self):
        """Test text generation with mocked responses."""
        provider = self._create_mock_provider({
            "response": "Mock generated text",
            "done": True,
            "usage": {"eval_count": 5}
        })
        
        prompt = "Tell me a joke."
        result = await provider.generate_text(self.test_model_name(), prompt)
        
        assert_valid_chat_response(result)
        assert "Mock generated text" in result["response"]
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_model_listing_unit(self):
        """Test model listing with mocked responses."""
        provider = self._create_mock_provider({
            "models": [
                {"name": "model1:latest", "size": 1000},
                {"name": "model2:7b", "size": 2000},
            ]
        })
        
        result = await provider.list_models()
        assert_valid_models_response(result)
        assert len(result["models"]) == 2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_embeddings_unit(self):
        """Test embeddings generation with mocked responses."""
        provider = self._create_mock_provider({
            "embedding": [0.1, 0.2, 0.3] * 100  # 300-dim vector
        })
        
        text = "Test text for embeddings"
        result = await provider.get_embeddings("embedding-model", text)
        
        assert_valid_embeddings_response(result)
        assert len(result["embedding"]) == 300
    
    # ========================================================================
    # Error handling tests
    # ========================================================================
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test handling of network errors."""
        provider = self._create_error_provider("network")
        
        with pytest.raises(Exception):  # Should be provider-specific exception
            await provider.list_models()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self):
        """Test handling of timeout errors."""
        provider = self._create_error_provider("timeout")
        
        with pytest.raises(Exception):  # Should be provider-specific exception
            messages = TestDataGenerator.chat_messages(1)
            await provider.chat_completion(self.test_model_name(), messages)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """Test handling of HTTP errors."""
        for status_code in [400, 401, 404, 429, 500, 503]:
            provider = self._create_error_provider("http", status_code)
            
            with pytest.raises(Exception):  # Should be provider-specific exception
                await provider.list_models()
    
    # ========================================================================
    # Streaming tests
    # ========================================================================
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_streaming_chat_unit(self):
        """Test streaming chat completion with mocked responses."""
        provider = self._create_streaming_provider([
            {"message": {"content": "Hello"}, "done": False},
            {"message": {"content": " there!"}, "done": False},
            {"message": {"content": ""}, "done": True},
        ])
        
        messages = TestDataGenerator.chat_messages(1)
        stream = provider.stream_chat_completion(self.test_model_name(), messages)
        
        chunks = await collect_stream(stream)
        assert len(chunks) >= 2  # At least some chunks
        assert chunks[-1]["done"] is True  # Last chunk should be done
        
        # Combine content
        content = "".join(chunk.get("message", {}).get("content", "") for chunk in chunks)
        assert content == "Hello there!"
    
    # ========================================================================
    # Helper methods
    # ========================================================================
    
    def _create_mock_provider(self, mock_response: Dict[str, Any]):
        """Create a provider with mocked HTTP responses."""
        provider_cls = self.provider_class()
        config = self.provider_config()
        provider = provider_cls(config)
        
        # Mock the session
        mock_session = AsyncMock()
        mock_http_response = AsyncMock()
        mock_http_response.status = 200
        mock_http_response.json.return_value = mock_response
        mock_session.request.return_value.__aenter__.return_value = mock_http_response
        
        provider._session = mock_session
        return provider
    
    def _create_error_provider(self, error_type: str, status_code: int = 500):
        """Create a provider that simulates errors."""
        provider_cls = self.provider_class()
        config = self.provider_config()
        provider = provider_cls(config)
        
        # Mock the session to raise errors
        mock_session = AsyncMock()
        
        if error_type == "network":
            import aiohttp
            mock_session.request.side_effect = aiohttp.ClientConnectorError(None, OSError("Network error"))
        elif error_type == "timeout":
            mock_session.request.side_effect = asyncio.TimeoutError("Request timeout")
        elif error_type == "http":
            mock_response = AsyncMock()
            mock_response.status = status_code
            mock_response.text.return_value = f"HTTP {status_code} Error"
            mock_session.request.return_value.__aenter__.return_value = mock_response
        
        provider._session = mock_session
        return provider
    
    def _create_streaming_provider(self, chunks: List[Dict[str, Any]]):
        """Create a provider with mocked streaming responses."""
        provider_cls = self.provider_class()
        config = self.provider_config()
        provider = provider_cls(config)
        
        # Mock streaming response
        async def mock_iter_chunked():
            for chunk in chunks:
                yield f"{chunk}\n".encode()
        
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content.iter_chunked.return_value = mock_iter_chunked()
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        provider._session = mock_session
        return provider


class BaseProviderIntegrationTest(ABC):
    """
    Base class for provider integration tests.
    
    These tests require actual service connectivity.
    """
    
    # ========================================================================
    # Abstract methods
    # ========================================================================
    
    @abstractmethod
    def provider_class(self) -> Type:
        """Return the provider class to test."""
        pass
    
    @abstractmethod
    def provider_config(self) -> Dict[str, Any]:
        """Return test configuration for the provider."""
        pass
    
    @abstractmethod
    def service_available(self) -> bool:
        """Check if the service is available for testing."""
        pass
    
    @abstractmethod
    def test_model_name(self) -> str:
        """Return name of model to use for testing."""
        pass
    
    # ========================================================================
    # Service connectivity tests
    # ========================================================================
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_service_connection(self):
        """Test basic connectivity to the service."""
        if not self.service_available():
            pytest.skip("Service not available")
            
        provider_cls = self.provider_class()
        config = self.provider_config()
        
        async with provider_cls(config) as provider:
            models = await provider.list_models()
            assert "models" in models
            assert isinstance(models["models"], list)
    
    # ========================================================================
    # Real model tests
    # ========================================================================
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_chat_completion(self):
        """Test chat completion with real model."""
        if not self.service_available():
            pytest.skip("Service not available")
            
        provider_cls = self.provider_class()
        config = self.provider_config()
        
        async with provider_cls(config) as provider:
            messages = [
                {"role": "user", "content": "Say 'Hello World' and nothing else."}
            ]
            
            result = await provider.chat_completion(self.test_model_name(), messages)
            assert_valid_chat_response(result)
            assert len(result["response"]) > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_streaming(self):
        """Test streaming with real model."""
        if not self.service_available():
            pytest.skip("Service not available")
            
        provider_cls = self.provider_class()
        config = self.provider_config()
        
        async with provider_cls(config) as provider:
            messages = [
                {"role": "user", "content": "Count from 1 to 3."}
            ]
            
            stream = provider.stream_chat_completion(self.test_model_name(), messages)
            chunks = await collect_stream(stream, max_items=20)
            
            assert len(chunks) > 0
            assert any(chunk.get("done", False) for chunk in chunks)
    
    # ========================================================================
    # Performance tests
    # ========================================================================
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_performance_chat_completion(self):
        """Test chat completion performance."""
        if not self.service_available():
            pytest.skip("Service not available")
            
        provider_cls = self.provider_class()
        config = self.provider_config()
        
        async with provider_cls(config) as provider:
            tracker = PerformanceTracker()
            tracker.start()
            
            messages = [
                {"role": "user", "content": "What is 2+2?"}
            ]
            
            result = await provider.chat_completion(self.test_model_name(), messages)
            tracker.record_first_response()
            
            metrics = tracker.stop()
            
            # Basic performance assertions (adjust thresholds as needed)
            assert metrics.total_time < 30.0, f"Request took {metrics.total_time:.2f}s"
            assert metrics.first_response_time < 30.0, f"First response took {metrics.first_response_time:.2f}s"
            
            assert_valid_chat_response(result)
    
    # ========================================================================
    # Concurrent execution tests
    # ========================================================================
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling multiple concurrent requests."""
        if not self.service_available():
            pytest.skip("Service not available")
            
        provider_cls = self.provider_class()
        config = self.provider_config()
        
        async with provider_cls(config) as provider:
            # Create multiple concurrent requests
            tasks = []
            for i in range(3):
                messages = [
                    {"role": "user", "content": f"Respond with just the number {i+1}"}
                ]
                task = provider.chat_completion(self.test_model_name(), messages)
                tasks.append(task)
            
            # Wait for all requests to complete
            results = await asyncio.gather(*tasks)
            
            # Verify all requests succeeded
            assert len(results) == 3
            for result in results:
                assert_valid_chat_response(result)


class BaseProviderBenchmarkTest(ABC):
    """
    Base class for provider benchmark tests.
    
    These tests focus on performance characteristics.
    """
    
    # ========================================================================
    # Abstract methods
    # ========================================================================
    
    @abstractmethod
    def provider_class(self) -> Type:
        """Return the provider class to test."""
        pass
    
    @abstractmethod
    def provider_config(self) -> Dict[str, Any]:
        """Return test configuration for the provider."""
        pass
    
    @abstractmethod
    def service_available(self) -> bool:
        """Check if the service is available for testing."""
        pass
    
    @abstractmethod
    def test_model_name(self) -> str:
        """Return name of model to use for testing."""
        pass
    
    # ========================================================================
    # Benchmark tests
    # ========================================================================
    
    @pytest.mark.benchmark
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_throughput_benchmark(self):
        """Benchmark request throughput."""
        if not self.service_available():
            pytest.skip("Service not available")
            
        provider_cls = self.provider_class()
        config = self.provider_config()
        
        async with provider_cls(config) as provider:
            requests_count = 10
            tracker = PerformanceTracker()
            tracker.start()
            
            # Sequential requests
            for i in range(requests_count):
                messages = [
                    {"role": "user", "content": f"Say hello {i}"}
                ]
                result = await provider.chat_completion(self.test_model_name(), messages)
                tracker.record_request(success="response" in result)
                
                if i == 0:
                    tracker.record_first_response()
            
            metrics = tracker.stop()
            
            # Calculate throughput
            requests_per_second = requests_count / metrics.total_time
            
            print(f"Throughput: {requests_per_second:.2f} requests/second")
            print(f"Average response time: {metrics.avg_response_time:.2f}s")
            print(f"Success rate: {metrics.success_rate:.2%}")
            
            # Basic assertions
            assert metrics.success_rate >= 0.8  # At least 80% success rate
            assert requests_per_second > 0  # Some throughput achieved
    
    @pytest.mark.benchmark
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_streaming_performance(self):
        """Benchmark streaming performance."""
        if not self.service_available():
            pytest.skip("Service not available")
            
        provider_cls = self.provider_class()
        config = self.provider_config()
        
        async with provider_cls(config) as provider:
            tracker = PerformanceTracker()
            tracker.start()
            
            messages = [
                {"role": "user", "content": "Count from 1 to 10 slowly."}
            ]
            
            chunks = []
            first_chunk = True
            
            async for chunk in provider.stream_chat_completion(self.test_model_name(), messages):
                if first_chunk:
                    tracker.record_first_response()
                    first_chunk = False
                    
                chunks.append(chunk)
                
                if chunk.get("done", False):
                    break
            
            metrics = tracker.stop()
            
            print(f"Total chunks: {len(chunks)}")
            print(f"Time to first chunk: {metrics.first_response_time:.2f}s")
            print(f"Total streaming time: {metrics.total_time:.2f}s")
            
            # Basic assertions
            assert len(chunks) > 1  # Should have multiple chunks
            assert metrics.first_response_time < 10.0  # First chunk within 10s
            assert metrics.total_time < 60.0  # Complete within 60s
