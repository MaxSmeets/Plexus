"""
Comprehensive integration tests for Ollama model provider.

This module provides complete integration test coverage for the Ollama provider
using the scalable testing framework and real Ollama service connectivity.
"""
import pytest
import asyncio
import sys
import os
from typing import Dict, Any, List, Type
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from model_providers.ollama.provider import OllamaProvider
from model_providers.ollama.config import OllamaConfig
from model_providers.ollama.base_provider import ChatMessage, MessageRole, ModelParameters
from model_providers.ollama.utils import OllamaError, ModelNotFoundError

# Import test framework
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from base_provider_tests import BaseProviderIntegrationTest, BaseProviderBenchmarkTest
from utils import (
    TestDataGenerator,
    PerformanceTracker,
    performance_test,
    collect_stream,
    assert_valid_chat_response,
    assert_valid_embeddings_response,
    assert_valid_models_response,
    requires_service,
)


# ============================================================================
# Service Availability Check
# ============================================================================

async def check_ollama_service() -> bool:
    """Check if Ollama service is available."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:11434/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
    except Exception:
        return False


async def get_ollama_models() -> List[str]:
    """Get available Ollama models."""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model["name"] for model in data.get("models", [])]
                return []
    except Exception:
        return []


# ============================================================================
# Ollama Integration Tests Using Scalable Framework
# ============================================================================

class TestOllamaIntegration(BaseProviderIntegrationTest):
    """
    Comprehensive Ollama integration tests using the scalable framework.
    
    These tests require a running Ollama instance with models installed.
    """
    
    # ========================================================================
    # Required implementations for base test class
    # ========================================================================
    
    def provider_class(self) -> Type:
        """Return the Ollama provider class."""
        return OllamaProvider
    
    def provider_config(self) -> Dict[str, Any]:
        """Return integration test configuration for Ollama."""
        return OllamaConfig(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            timeout=60.0,  # Longer timeout for integration tests
            max_retries=2,
            verify_ssl=False
        )
    
    def service_available(self) -> bool:
        """Check if Ollama service is available."""
        return asyncio.run(check_ollama_service())
    
    def test_model_name(self) -> str:
        """Return test model name (prefer llama3.2:latest if available)."""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                models = [model["name"] for model in models_data.get("models", [])]
                if "llama3.2:latest" in models:
                    return "llama3.2:latest"
                elif any("llama" in model for model in models):
                    return next(model for model in models if "llama" in model)
                elif models:
                    return models[0]
        except Exception:
            pass
        return "llama3.2:latest"  # Default fallback
    
    # ========================================================================
    # Setup and Teardown
    # ========================================================================
    
    @pytest.fixture(scope="class", autouse=True)
    async def setup_integration_tests(self):
        """Setup for integration tests."""
        if not self.service_available():
            pytest.skip("Ollama service not available at localhost:11434")
        
        # Verify at least one model is available
        models = await get_ollama_models()
        if not models:
            pytest.skip("No Ollama models available for testing")
            
        print(f"Running Ollama integration tests with models: {models}")
        yield
        print("Ollama integration tests completed")
    
    # ========================================================================
    # Enhanced Integration Tests
    # ========================================================================
    
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_ollama_service_health(self):
        """Test Ollama service health and availability."""
        config = self.provider_config()
        
        async with OllamaProvider(config) as provider:
            # Test basic connectivity
            models = await provider.list_models()
            assert_valid_models_response(models)
            assert len(models["models"]) > 0
            
            print(f"Ollama service healthy with {len(models['models'])} models")
    
    @pytest.mark.integration 
    @pytest.mark.ollama
    async def test_ollama_model_discovery(self):
        """Test automatic model discovery and selection."""
        config = self.provider_config()
        
        async with OllamaProvider(config) as provider:
            models_response = await provider.list_models()
            models = [model["name"] for model in models_response["models"]]
            
            # Check for expected model categories
            text_models = [m for m in models if any(keyword in m.lower() for keyword in ["llama", "mistral", "gemma", "qwen"])]
            embed_models = [m for m in models if any(keyword in m.lower() for keyword in ["embed", "nomic"])]
            
            assert len(text_models) > 0, f"No text generation models found. Available: {models}"
            
            print(f"Text models: {text_models}")
            print(f"Embedding models: {embed_models}")
    
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_ollama_chat_conversation_flow(self):
        """Test complete conversation flow with context preservation."""
        if not self.service_available():
            pytest.skip("Ollama service not available")
            
        config = self.provider_config()
        model = self.test_model_name()
        
        async with OllamaProvider(config) as provider:
            # Multi-turn conversation
            messages = [
                ChatMessage(role=MessageRole.USER, content="My name is Alice. Remember this."),
            ]
            
            # First exchange
            result1 = await provider.chat_completion(model, messages)
            assert_valid_chat_response(result1)
            
            # Add assistant response and continue conversation
            messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=result1["response"]))
            messages.append(ChatMessage(role=MessageRole.USER, content="What is my name?"))
            
            result2 = await provider.chat_completion(model, messages)
            assert_valid_chat_response(result2)
            
            # The model should remember the name from context
            response_lower = result2["response"].lower()
            assert "alice" in response_lower, f"Model should remember name 'Alice'. Response: {result2['response']}"
            
            print(f"Conversation test passed. Model remembered context correctly.")
    
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_ollama_different_model_parameters(self):
        """Test various model parameter configurations."""
        if not self.service_available():
            pytest.skip("Ollama service not available")
            
        config = self.provider_config()
        model = self.test_model_name()
        
        async with OllamaProvider(config) as provider:
            base_message = [ChatMessage(role=MessageRole.USER, content="Give me a very short response about the weather.")]
            
            # Test different temperature values
            for temp in [0.1, 0.5, 0.9]:
                params = ModelParameters(temperature=temp, max_tokens=20)
                result = await provider.chat_completion(model, base_message, params)
                assert_valid_chat_response(result)
                assert len(result["response"]) > 0
                
                print(f"Temperature {temp}: {len(result['response'])} chars")
            
            # Test token limits
            for max_tokens in [10, 50, 100]:
                params = ModelParameters(max_tokens=max_tokens)
                result = await provider.chat_completion(model, base_message, params)
                assert_valid_chat_response(result)
                
                print(f"Max tokens {max_tokens}: {len(result['response'])} chars")
    
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_ollama_streaming_quality(self):
        """Test streaming response quality and consistency."""
        if not self.service_available():
            pytest.skip("Ollama service not available")
            
        config = self.provider_config()
        model = self.test_model_name()
        
        async with OllamaProvider(config) as provider:
            messages = [ChatMessage(role=MessageRole.USER, content="Count from 1 to 5, one number per line.")]
            
            chunks = []
            content_parts = []
            first_chunk_time = None
            start_time = time.time()
            
            async for chunk in provider.stream_chat_completion(model, messages):
                if first_chunk_time is None:
                    first_chunk_time = time.time() - start_time
                    
                chunks.append(chunk)
                
                if "message" in chunk and "content" in chunk["message"]:
                    content_parts.append(chunk["message"]["content"])
                
                if chunk.get("done", False):
                    break
            
            total_time = time.time() - start_time
            full_response = "".join(content_parts)
            
            # Assertions
            assert len(chunks) > 1, "Should receive multiple chunks"
            assert any(chunk.get("done", False) for chunk in chunks), "Should have a 'done' chunk"
            assert first_chunk_time < 10.0, f"First chunk took {first_chunk_time:.2f}s (too slow)"
            assert len(full_response) > 0, "Should have accumulated content"
            
            # Check for numbers in response (loose validation)
            assert any(str(i) in full_response for i in range(1, 6)), "Should contain counting numbers"
            
            print(f"Streaming test: {len(chunks)} chunks, {first_chunk_time:.2f}s to first chunk")
            print(f"Full response: {full_response[:100]}...")
    
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_ollama_embeddings_integration(self):
        """Test embeddings generation with real embedding models."""
        if not self.service_available():
            pytest.skip("Ollama service not available")
            
        config = self.provider_config()
        
        async with OllamaProvider(config) as provider:
            # Get available models
            models_response = await provider.list_models()
            models = [model["name"] for model in models_response["models"]]
            
            # Find an embedding model
            embedding_models = [
                model for model in models 
                if any(keyword in model.lower() for keyword in ["embed", "nomic", "sentence"])
            ]
            
            if not embedding_models:
                pytest.skip("No embedding models available")
            
            embedding_model = embedding_models[0]
            print(f"Testing embeddings with model: {embedding_model}")
            
            # Test embedding generation
            test_texts = [
                "This is a test sentence.",
                "Another different sentence for comparison.",
                "The quick brown fox jumps over the lazy dog."
            ]
            
            embeddings = []
            for text in test_texts:
                result = await provider.get_embeddings(embedding_model, text)
                assert_valid_embeddings_response(result)
                embeddings.append(result["embedding"])
                
                print(f"Generated embedding of dimension {len(result['embedding'])} for text: {text[:30]}...")
            
            # Basic validation
            assert len(embeddings) == 3
            assert all(len(emb) == len(embeddings[0]) for emb in embeddings), "All embeddings should have same dimension"
            assert all(len(emb) > 100 for emb in embeddings), "Embeddings should be reasonably high-dimensional"
            
            # Embeddings should be different for different texts
            assert embeddings[0] != embeddings[1], "Different texts should produce different embeddings"
    
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_ollama_error_handling_integration(self):
        """Test error handling with real service responses."""
        if not self.service_available():
            pytest.skip("Ollama service not available")
            
        config = self.provider_config()
        
        async with OllamaProvider(config) as provider:
            # Test with non-existent model
            with pytest.raises((OllamaError, ModelNotFoundError)):
                await provider.chat_completion(
                    "definitely-nonexistent-model:latest",
                    [ChatMessage(role=MessageRole.USER, content="Hello")]
                )
            
            # Test with empty messages (should be caught by validation)
            with pytest.raises(ValueError):
                await provider.chat_completion(self.test_model_name(), [])
            
            print("Error handling tests passed - proper exceptions raised for invalid requests")
    
    @pytest.mark.integration
    @pytest.mark.ollama
    @pytest.mark.slow
    async def test_ollama_concurrent_requests(self):
        """Test handling of concurrent requests."""
        if not self.service_available():
            pytest.skip("Ollama service not available")
            
        config = self.provider_config()
        model = self.test_model_name()
        
        async with OllamaProvider(config) as provider:
            # Create multiple concurrent requests
            request_count = 5
            tasks = []
            
            for i in range(request_count):
                messages = [ChatMessage(role=MessageRole.USER, content=f"Respond with the number {i+1} only.")]
                task = provider.chat_completion(model, messages)
                tasks.append(task)
            
            # Execute concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Analyze results
            successful_results = [r for r in results if isinstance(r, dict) and "response" in r]
            errors = [r for r in results if isinstance(r, Exception)]
            
            print(f"Concurrent test: {len(successful_results)}/{request_count} successful in {total_time:.2f}s")
            
            # At least some requests should succeed
            assert len(successful_results) >= request_count * 0.6, f"At least 60% of requests should succeed, got {len(successful_results)}/{request_count}"
            
            # Check responses are valid
            for result in successful_results:
                assert_valid_chat_response(result)
                assert len(result["response"]) > 0
            
            if errors:
                print(f"Encountered {len(errors)} errors during concurrent execution: {[str(e) for e in errors]}")
    
    @pytest.mark.integration
    @pytest.mark.ollama
    async def test_ollama_large_context_handling(self):
        """Test handling of large context/prompts."""
        if not self.service_available():
            pytest.skip("Ollama service not available")
            
        config = self.provider_config()
        model = self.test_model_name()
        
        async with OllamaProvider(config) as provider:
            # Create a reasonably large prompt
            large_prompt = """
            Please analyze the following text and provide a summary. Here is a long text that contains
            multiple paragraphs and various topics to test the model's ability to handle larger contexts.
            
            """ + "This is repeated content for context testing. " * 100
            
            messages = [ChatMessage(role=MessageRole.USER, content=large_prompt)]
            
            start_time = time.time()
            result = await provider.chat_completion(model, messages)
            processing_time = time.time() - start_time
            
            assert_valid_chat_response(result)
            assert len(result["response"]) > 0
            
            print(f"Large context test: {len(large_prompt)} chars input → {len(result['response'])} chars output in {processing_time:.2f}s")
            
            # Should complete within reasonable time (adjust based on your hardware)
            assert processing_time < 120.0, f"Large context processing took {processing_time:.2f}s (too slow)"


# ============================================================================
# Ollama Performance/Benchmark Tests
# ============================================================================

class TestOllamaBenchmarks(BaseProviderBenchmarkTest):
    """
    Performance and benchmark tests for Ollama provider.
    
    These tests focus on performance characteristics and are marked as slow.
    """
    
    # ========================================================================
    # Required implementations for base test class
    # ========================================================================
    
    def provider_class(self) -> Type:
        """Return the Ollama provider class."""
        return OllamaProvider
    
    def provider_config(self) -> Dict[str, Any]:
        """Return benchmark configuration for Ollama."""
        return OllamaConfig(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            timeout=120.0,  # Extended timeout for benchmarks
            max_retries=1,   # Fewer retries for accurate timing
            verify_ssl=False
        )
    
    def service_available(self) -> bool:
        """Check if Ollama service is available."""
        return asyncio.run(check_ollama_service())
    
    def test_model_name(self) -> str:
        """Return test model name for benchmarks."""
        models = asyncio.run(get_ollama_models())
        # Prefer smaller/faster models for benchmarks
        for preferred in ["llama3.2:1b", "phi3:mini", "qwen2:0.5b"]:
            if preferred in models:
                return preferred
        # Fallback to any available model
        return next(iter(models), "llama3.2:latest")
    
    # ========================================================================
    # Ollama-Specific Benchmark Tests
    # ========================================================================
    
    @pytest.mark.benchmark
    @pytest.mark.ollama
    @pytest.mark.slow
    async def test_ollama_response_time_benchmark(self):
        """Benchmark response times for different prompt types."""
        if not self.service_available():
            pytest.skip("Ollama service not available")
            
        config = self.provider_config()
        model = self.test_model_name()
        
        async with OllamaProvider(config) as provider:
            prompts = {
                "simple": "Say hello.",
                "reasoning": "What is 15 * 23? Show your work.",
                "creative": "Write a haiku about programming.",
                "factual": "What is the capital of France and when was it founded?",
            }
            
            results = {}
            
            for prompt_type, prompt in prompts.items():
                async with performance_test({"max_time": 30.0}) as tracker:
                    messages = [ChatMessage(role=MessageRole.USER, content=prompt)]
                    result = await provider.chat_completion(model, messages)
                    tracker.record_first_response()
                    
                    assert_valid_chat_response(result)
                    metrics = tracker.stop()
                    
                    results[prompt_type] = {
                        "time": metrics.total_time,
                        "response_length": len(result["response"]),
                        "response": result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
                    }
                    
                    print(f"{prompt_type.capitalize()} prompt: {metrics.total_time:.2f}s, {len(result['response'])} chars")
            
            # Basic performance assertions
            assert all(r["time"] < 30.0 for r in results.values()), "All responses should complete within 30s"
            assert all(r["response_length"] > 0 for r in results.values()), "All responses should have content"
            
            # Simple prompts should generally be faster
            if "simple" in results and "reasoning" in results:
                # Allow some variance, but simple should generally be faster or similar
                assert results["simple"]["time"] <= results["reasoning"]["time"] * 1.5, "Simple prompts should be reasonably fast"
    
    @pytest.mark.benchmark
    @pytest.mark.ollama
    @pytest.mark.slow
    async def test_ollama_streaming_performance_benchmark(self):
        """Benchmark streaming response performance."""
        if not self.service_available():
            pytest.skip("Ollama service not available")
            
        config = self.provider_config()
        model = self.test_model_name()
        
        async with OllamaProvider(config) as provider:
            messages = [ChatMessage(role=MessageRole.USER, content="Count from 1 to 10, explaining each number briefly.")]
            
            metrics = {
                "chunks": [],
                "first_chunk_time": None,
                "total_time": None,
                "content_length": 0,
            }
            
            start_time = time.time()
            
            async for chunk in provider.stream_chat_completion(model, messages):
                current_time = time.time() - start_time
                
                if metrics["first_chunk_time"] is None:
                    metrics["first_chunk_time"] = current_time
                
                metrics["chunks"].append({
                    "timestamp": current_time,
                    "chunk": chunk,
                })
                
                if "message" in chunk and "content" in chunk["message"]:
                    metrics["content_length"] += len(chunk["message"]["content"])
                
                if chunk.get("done", False):
                    break
            
            metrics["total_time"] = time.time() - start_time
            
            # Performance analysis
            chunk_count = len(metrics["chunks"])
            avg_chunk_interval = metrics["total_time"] / max(chunk_count - 1, 1)  # Exclude final 'done' chunk
            
            print(f"Streaming benchmark:")
            print(f"  Total chunks: {chunk_count}")
            print(f"  First chunk: {metrics['first_chunk_time']:.3f}s")
            print(f"  Total time: {metrics['total_time']:.2f}s")
            print(f"  Content length: {metrics['content_length']} chars")
            print(f"  Avg chunk interval: {avg_chunk_interval:.3f}s")
            print(f"  Chars per second: {metrics['content_length'] / metrics['total_time']:.1f}")
            
            # Performance assertions
            assert metrics["first_chunk_time"] < 10.0, f"First chunk took {metrics['first_chunk_time']:.2f}s (too slow)"
            assert metrics["total_time"] < 60.0, f"Total streaming took {metrics['total_time']:.2f}s (too slow)"
            assert chunk_count > 3, f"Should have multiple chunks for long response, got {chunk_count}"
            assert metrics["content_length"] > 50, f"Should generate substantial content, got {metrics['content_length']} chars"
    
    @pytest.mark.benchmark
    @pytest.mark.ollama
    @pytest.mark.slow
    async def test_ollama_model_switching_benchmark(self):
        """Benchmark performance when switching between different models."""
        if not self.service_available():
            pytest.skip("Ollama service not available")
            
        config = self.provider_config()
        available_models = await get_ollama_models()
        
        if len(available_models) < 2:
            pytest.skip("Need at least 2 models for model switching benchmark")
        
        # Use up to 3 models for the test
        test_models = available_models[:3]
        
        async with OllamaProvider(config) as provider:
            prompt = "What is 2+2?"
            messages = [ChatMessage(role=MessageRole.USER, content=prompt)]
            
            results = {}
            
            for model in test_models:
                model_times = []
                
                # Test each model multiple times
                for i in range(3):
                    start_time = time.time()
                    result = await provider.chat_completion(model, messages)
                    response_time = time.time() - start_time
                    
                    assert_valid_chat_response(result)
                    model_times.append(response_time)
                
                avg_time = sum(model_times) / len(model_times)
                results[model] = {
                    "times": model_times,
                    "avg_time": avg_time,
                    "min_time": min(model_times),
                    "max_time": max(model_times),
                }
                
                print(f"Model {model}: avg {avg_time:.2f}s (range: {min(model_times):.2f}s - {max(model_times):.2f}s)")
            
            # Analysis
            fastest_model = min(results.keys(), key=lambda m: results[m]["avg_time"])
            slowest_model = max(results.keys(), key=lambda m: results[m]["avg_time"])
            
            print(f"Fastest model: {fastest_model} ({results[fastest_model]['avg_time']:.2f}s avg)")
            print(f"Slowest model: {slowest_model} ({results[slowest_model]['avg_time']:.2f}s avg)")
            
            # Basic assertions
            assert all(r["avg_time"] < 30.0 for r in results.values()), "All models should respond within 30s on average"
    
    @pytest.mark.benchmark
    @pytest.mark.ollama  
    @pytest.mark.slow
    async def test_ollama_memory_usage_benchmark(self):
        """Benchmark memory usage patterns during extended operation."""
        if not self.service_available():
            pytest.skip("Ollama service not available")
            
        config = self.provider_config()
        model = self.test_model_name()
        
        async with OllamaProvider(config) as provider:
            # Test with varying conversation lengths
            base_messages = [
                ChatMessage(role=MessageRole.USER, content="Let's have a conversation."),
                ChatMessage(role=MessageRole.ASSISTANT, content="Sure! I'd be happy to chat."),
            ]
            
            conversation_lengths = [1, 5, 10, 15]  # Number of exchanges
            
            for length in conversation_lengths:
                messages = base_messages.copy()
                
                # Build up conversation
                for i in range(length):
                    messages.append(ChatMessage(role=MessageRole.USER, content=f"Tell me about topic number {i+1}."))
                    
                    start_time = time.time()
                    result = await provider.chat_completion(model, messages)
                    response_time = time.time() - start_time
                    
                    assert_valid_chat_response(result)
                    messages.append(ChatMessage(role=MessageRole.ASSISTANT, content=result["response"]))
                    
                    total_chars = sum(len(msg.content) for msg in messages)
                    print(f"Conversation length {len(messages)} messages ({total_chars} chars): {response_time:.2f}s")
                
                # Performance should not degrade significantly with longer conversations
                # (This is a basic check - real memory profiling would require additional tools)
                assert response_time < 45.0, f"Long conversation response time {response_time:.2f}s too slow"


# ============================================================================
# Standalone Integration Test Runner
# ============================================================================

if __name__ == "__main__":
    """Run integration tests directly for quick validation."""
    
    async def main():
        """Run basic integration test."""
        print("Running Ollama integration test...")
        
        # Check service availability
        if not await check_ollama_service():
            print("❌ Ollama service not available at localhost:11434")
            return False
        
        print("✅ Ollama service is available")
        
        # Get available models
        models = await get_ollama_models()
        if not models:
            print("❌ No models available")
            return False
        
        print(f"✅ Found {len(models)} models: {models}")
        
        # Test basic functionality
        config = OllamaConfig()
        test_model = models[0] if "llama3.2:latest" not in models else "llama3.2:latest"
        
        try:
            async with OllamaProvider(config) as provider:
                # Test chat completion
                messages = [ChatMessage(role=MessageRole.USER, content="Say 'Integration test successful'")]
                result = await provider.chat_completion(test_model, messages)
                
                print(f"✅ Chat completion test passed: {result['response']}")
                
                # Test streaming
                stream_messages = [ChatMessage(role=MessageRole.USER, content="Count 1, 2, 3")]
                chunks = []
                async for chunk in provider.stream_chat_completion(test_model, stream_messages):
                    chunks.append(chunk)
                    if chunk.get("done", False):
                        break
                
                print(f"✅ Streaming test passed: {len(chunks)} chunks received")
                
                print("🎉 All integration tests passed!")
                return True
                
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            return False
    
    # Run the test
    success = asyncio.run(main())
    exit(0 if success else 1)
