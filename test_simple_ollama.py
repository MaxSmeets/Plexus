"""Simple integration test to verify Ollama provider works."""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from model_providers.ollama.provider import OllamaProvider
from model_providers.ollama.config import OllamaConfig
from model_providers.ollama.base_provider import ChatMessage, MessageRole

@pytest.mark.asyncio
@pytest.mark.integration
async def test_simple_ollama_connection():
    """Test basic Ollama provider functionality."""
    config = OllamaConfig(
        base_url="http://localhost:11434",
        timeout=10.0
    )
    
    provider = OllamaProvider(config)
    
    try:
        # Test basic connectivity by listing models
        models = await provider.list_models()
        assert "models" in models
        assert isinstance(models["models"], list)
        
        print(f"Available models: {[m.get('name', 'Unknown') for m in models['models']]}")
        
    finally:
        await provider.close()

@pytest.mark.asyncio  
@pytest.mark.integration
async def test_simple_ollama_chat():
    """Test basic chat functionality."""
    config = OllamaConfig(
        base_url="http://localhost:11434",
        timeout=30.0
    )
    
    provider = OllamaProvider(config)
    
    try:
        # Get available models first
        models = await provider.list_models()
        if not models["models"]:
            pytest.skip("No models available in Ollama")
            
        model_name = models["models"][0]["name"]
        print(f"Testing with model: {model_name}")
        
        # Test simple chat
        response = await provider.chat_completion(
            model=model_name,
            messages=[ChatMessage(role=MessageRole.USER, content="Say hello")]
        )
        
        assert "choices" in response
        assert len(response["choices"]) > 0
        assert "message" in response["choices"][0]
        assert "content" in response["choices"][0]["message"]
        
        print(f"Chat response: {response['choices'][0]['message']['content']}")
        
    finally:
        await provider.close()
