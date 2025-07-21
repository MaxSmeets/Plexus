"""
Example usage of the Ollama model provider.

This script demonstrates how to use the OllamaProvider class for various tasks
including chat completions, text generation, and embeddings.
"""

import asyncio
import json
from typing import List

from .provider import OllamaProvider
from .config import OllamaConfig
from ..base_provider import ChatMessage, ModelParameters, MessageRole


async def example_chat_completion():
    """Example of using chat completion with streaming."""
    print("=== Chat Completion Example ===")
    
    # Create configuration
    config = OllamaConfig(
        base_url="http://localhost:11434",
        timeout=300,
        keep_alive="5m"
    )
    
    # Initialize provider
    provider = OllamaProvider(config.to_dict())
    
    try:
        # Initialize the provider
        if not await provider.initialize():
            print("Failed to initialize Ollama provider")
            return
        
        # List available models
        models = await provider.list_models()
        print(f"Available models: {models}")
        
        if "llama3.2:latest" not in models:
            print("llama3.2:latest not found. Please ensure it's installed.")
            return
        
        # Prepare chat messages
        messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="You are a helpful AI assistant."
            ),
            ChatMessage(
                role=MessageRole.USER,
                content="Explain quantum computing in simple terms."
            )
        ]
        
        # Set parameters for generation
        parameters = ModelParameters(
            temperature=0.7,
            top_p=0.9,
            stream=True,
            max_tokens=500
        )
        
        # Generate streaming response
        print("\\nGenerating response...")
        response_chunks = await provider.generate_chat(
            messages=messages,
            model="llama3.2:latest",
            parameters=parameters
        )
        
        full_response = ""
        async for chunk in response_chunks:
            if chunk.content:
                print(chunk.content, end="", flush=True)
                full_response += chunk.content
            
            if chunk.is_final and chunk.metadata:
                print("\\n\\nGeneration metrics:")
                tokens_per_sec = chunk.metadata.get("eval_count", 0) / (
                    chunk.metadata.get("eval_duration", 1) / 1_000_000_000
                )
                print(f"Tokens per second: {tokens_per_sec:.2f}")
                print(f"Total tokens: {chunk.metadata.get('eval_count', 0)}")
        
        print("\\n")
        
    except Exception as e:
        print(f"Error during chat completion: {e}")
    
    finally:
        await provider.close()


async def example_text_completion():
    """Example of using text completion without streaming."""
    print("\\n=== Text Completion Example ===")
    
    config = OllamaConfig()
    provider = OllamaProvider(config.to_dict())
    
    try:
        if not await provider.initialize():
            print("Failed to initialize Ollama provider")
            return
        
        # Generate non-streaming completion
        parameters = ModelParameters(
            temperature=0.5,
            stream=False,
            max_tokens=200
        )
        
        response = await provider.generate_completion(
            prompt="The future of artificial intelligence is",
            model="llama3.2:latest",
            parameters=parameters
        )
        
        print(f"Completion: {response.content}")
        print(f"Model: {response.model}")
        print(f"Tokens used: {response.token_usage}")
        
    except Exception as e:
        print(f"Error during text completion: {e}")
    
    finally:
        await provider.close()


async def example_embeddings():
    """Example of generating embeddings."""
    print("\\n=== Embeddings Example ===")
    
    config = OllamaConfig()
    provider = OllamaProvider(config.to_dict())
    
    try:
        if not await provider.initialize():
            print("Failed to initialize Ollama provider")
            return
        
        # Check for embedding models
        models = await provider.list_models()
        embedding_models = [m for m in models if "embed" in m.lower() or "minilm" in m.lower()]
        
        if not embedding_models:
            print("No embedding models found. Please install an embedding model like 'all-minilm'")
            return
        
        embedding_model = embedding_models[0]
        print(f"Using embedding model: {embedding_model}")
        
        # Generate embeddings
        texts = [
            "The quick brown fox jumps over the lazy dog",
            "Machine learning is a subset of artificial intelligence",
            "Python is a popular programming language"
        ]
        
        embeddings = await provider.generate_embeddings(
            texts=texts,
            model=embedding_model
        )
        
        print(f"Generated {len(embeddings)} embeddings")
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            print(f"Text {i+1}: {text}")
            print(f"Embedding dimensions: {len(embedding)}")
            print(f"First 5 values: {embedding[:5]}")
            print()
        
    except Exception as e:
        print(f"Error during embedding generation: {e}")
    
    finally:
        await provider.close()


async def example_model_management():
    """Example of model management operations."""
    print("\\n=== Model Management Example ===")
    
    config = OllamaConfig()
    provider = OllamaProvider(config.to_dict())
    
    try:
        if not await provider.initialize():
            print("Failed to initialize Ollama provider")
            return
        
        # List all models
        models = await provider.list_models()
        print(f"Total models: {len(models)}")
        
        # List running models
        running_models = await provider.list_running_models()
        print(f"Running models: {len(running_models)}")
        
        # Get detailed info about a model
        if models:
            model_name = models[0]
            print(f"\\nGetting info for model: {model_name}")
            
            try:
                model_info = await provider.get_model_info(model_name)
                print(f"Model family: {model_info.get('details', {}).get('family', 'unknown')}")
                print(f"Parameter size: {model_info.get('details', {}).get('parameter_size', 'unknown')}")
                print(f"Quantization: {model_info.get('details', {}).get('quantization_level', 'unknown')}")
            except Exception as e:
                print(f"Could not get model info: {e}")
        
        # Health check
        health = await provider.health_check()
        print(f"\\nHealth check: {health}")
        
    except Exception as e:
        print(f"Error during model management: {e}")
    
    finally:
        await provider.close()


async def example_multimodal():
    """Example of multimodal (text + image) input."""
    print("\\n=== Multimodal Example ===")
    
    config = OllamaConfig()
    provider = OllamaProvider(config.to_dict())
    
    try:
        if not await provider.initialize():
            print("Failed to initialize Ollama provider")
            return
        
        # Check for multimodal models
        models = await provider.list_models()
        multimodal_models = [m for m in models if "llava" in m.lower()]
        
        if not multimodal_models:
            print("No multimodal models found. Please install a multimodal model like 'llava'")
            return
        
        model_name = multimodal_models[0]
        print(f"Using multimodal model: {model_name}")
        
        # Example with base64 encoded image (placeholder)
        # In a real scenario, you would encode an actual image
        placeholder_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        messages = [
            ChatMessage(
                role=MessageRole.USER,
                content="What do you see in this image?",
                images=[placeholder_image]
            )
        ]
        
        # Note: This is just an example structure
        # You would need a real image and a properly installed multimodal model
        print("Multimodal functionality available but requires actual image data and multimodal model")
        
    except Exception as e:
        print(f"Error during multimodal example: {e}")
    
    finally:
        await provider.close()


async def main():
    """Run all examples."""
    print("Ollama Provider Examples")
    print("=" * 40)
    
    try:
        await example_chat_completion()
        await example_text_completion()
        await example_embeddings()
        await example_model_management()
        await example_multimodal()
        
    except KeyboardInterrupt:
        print("\\nExamples interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
