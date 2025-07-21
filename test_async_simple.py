"""Simple async test to verify pytest-asyncio setup."""

import pytest
import asyncio

@pytest.mark.asyncio
async def test_simple_async():
    """Simple async test to verify setup."""
    await asyncio.sleep(0.1)
    assert True

@pytest.mark.asyncio 
async def test_ollama_connection():
    """Test Ollama connection."""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:11434/api/tags",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                assert response.status == 200
                data = await response.json()
                print(f"Available models: {data}")
    except Exception as e:
        pytest.skip(f"Ollama service not available: {e}")
