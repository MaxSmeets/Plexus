# Ollama Model Provider

This is the Ollama integration for the Plexus agentic system, providing access to local language models through Ollama's REST API.

## Features

- **Chat Completions**: Support for conversational AI with message history
- **Text Generation**: Simple prompt-to-text generation
- **Embeddings**: Generate vector embeddings for semantic search
- **Streaming**: Real-time response streaming for better user experience
- **Model Management**: List, pull, delete, and get information about models
- **Multimodal Support**: Text + image input for compatible models (e.g., LLaVA)
- **Error Handling**: Robust error handling with retry mechanisms
- **Configuration**: Flexible configuration through environment variables or config files

## Prerequisites

1. **Ollama Installation**: Install Ollama from [https://ollama.com](https://ollama.com)
2. **Running Ollama**: Ensure Ollama is running (default: `http://localhost:11434`)
3. **Models**: At least one model installed (e.g., `ollama pull llama3.2`)

## Quick Start

### Basic Setup

```python
import asyncio
from ollama import OllamaProvider, OllamaConfig
from base_provider import ChatMessage, ModelParameters, MessageRole

async def main():
    # Create configuration
    config = OllamaConfig(
        base_url="http://localhost:11434",
        timeout=300,
        keep_alive="5m"
    )
    
    # Initialize provider
    provider = OllamaProvider(config.to_dict())
    
    try:
        # Initialize connection
        if not await provider.initialize():
            print("Failed to connect to Ollama")
            return
        
        # List available models
        models = await provider.list_models()
        print(f"Available models: {models}")
        
        # Simple chat
        messages = [
            ChatMessage(role=MessageRole.USER, content="Hello!")
        ]
        
        response = await provider.generate_chat(
            messages=messages,
            model="llama3.2:latest",
            parameters=ModelParameters(stream=False)
        )
        
        print(f"Response: {response.content}")
        
    finally:
        await provider.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Environment Configuration

Set environment variables for easy configuration:

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_TIMEOUT="300"
export OLLAMA_KEEP_ALIVE="5m"
export OLLAMA_MAX_RETRIES="3"
```

## API Reference

### OllamaProvider

Main class for interacting with Ollama.

#### Methods

- `initialize()` - Initialize the provider and test connection
- `list_models()` - List all available models
- `generate_chat(messages, model, parameters)` - Generate chat completions
- `generate_completion(prompt, model, parameters)` - Generate text completions
- `generate_embeddings(texts, model)` - Generate embeddings
- `pull_model(model)` - Download a model from Ollama library
- `delete_model(model)` - Delete a model
- `get_model_info(model)` - Get detailed model information
- `list_running_models()` - List models currently loaded in memory
- `health_check()` - Check provider health status
- `close()` - Clean up resources

### Configuration

#### OllamaConfig

Configuration class with the following options:

- `base_url` (str): Ollama server URL (default: "http://localhost:11434")
- `timeout` (int): Request timeout in seconds (default: 300)
- `keep_alive` (str): How long to keep models loaded (default: "5m")
- `max_retries` (int): Maximum retry attempts (default: 3)
- `retry_delay` (float): Delay between retries (default: 1.0)
- `verify_ssl` (bool): Verify SSL certificates (default: True)

#### ModelParameters

Parameters for model generation:

- `temperature` (float): Randomness (0.0-2.0, default: 0.7)
- `top_p` (float): Nucleus sampling (0.0-1.0, default: 0.9)
- `top_k` (int): Top-k sampling (optional)
- `max_tokens` (int): Maximum tokens to generate (optional)
- `stream` (bool): Enable streaming (default: True)
- `stop_sequences` (List[str]): Stop generation at these sequences
- `seed` (int): Random seed for reproducible outputs
- `extra_params` (Dict): Additional model-specific parameters

## Examples

### Streaming Chat

```python
async def streaming_chat():
    provider = OllamaProvider(config.to_dict())
    await provider.initialize()
    
    messages = [
        ChatMessage(role=MessageRole.USER, content="Explain quantum computing")
    ]
    
    response_stream = await provider.generate_chat(
        messages=messages,
        model="llama3.2:latest",
        parameters=ModelParameters(stream=True, temperature=0.7)
    )
    
    async for chunk in response_stream:
        print(chunk.content, end="", flush=True)
        if chunk.is_final:
            print(f"\\nTokens/sec: {chunk.metadata.get('tokens_per_sec', 0)}")
```

### Embeddings

```python
async def generate_embeddings():
    provider = OllamaProvider(config.to_dict())
    await provider.initialize()
    
    texts = [
        "Machine learning is fascinating",
        "I love programming in Python",
        "The weather is nice today"
    ]
    
    embeddings = await provider.generate_embeddings(
        texts=texts,
        model="all-minilm:latest"
    )
    
    for text, embedding in zip(texts, embeddings):
        print(f"Text: {text}")
        print(f"Embedding dimensions: {len(embedding)}")
```

### Multimodal (Text + Image)

```python
async def multimodal_chat():
    provider = OllamaProvider(config.to_dict())
    await provider.initialize()
    
    # Encode image as base64
    import base64
    with open("image.jpg", "rb") as f:
        image_data = base64.b64encode(f.read()).decode()
    
    messages = [
        ChatMessage(
            role=MessageRole.USER,
            content="What do you see in this image?",
            images=[image_data]
        )
    ]
    
    response = await provider.generate_chat(
        messages=messages,
        model="llava:latest"
    )
    
    print(response.content)
```

## Model Management

### Installing Models

```bash
# Install a specific model
ollama pull llama3.2:latest

# Install an embedding model
ollama pull all-minilm:latest

# Install a multimodal model
ollama pull llava:latest
```

### Recommended Models

- **Chat/Text Generation**: `llama3.2:latest`, `mistral:latest`, `codellama:latest`
- **Embeddings**: `all-minilm:latest`, `nomic-embed-text:latest`
- **Multimodal**: `llava:latest`, `bakllava:latest`

## Testing

Run the basic test suite to verify your setup:

```python
from ollama.test_basic import run_tests
import asyncio

# Run all tests
asyncio.run(run_tests())
```

Or use the test script directly:

```bash
python -m ollama.test_basic
```

## Error Handling

The provider includes comprehensive error handling:

```python
from ollama import OllamaError, ModelNotFoundError, ConnectionError

try:
    response = await provider.generate_chat(messages, "nonexistent-model")
except ModelNotFoundError:
    print("Model not found")
except ConnectionError:
    print("Cannot connect to Ollama")
except OllamaError as e:
    print(f"Ollama error: {e}")
```

## Performance Tips

1. **Keep Models Loaded**: Use appropriate `keep_alive` settings to avoid reload delays
2. **Streaming**: Use streaming for long responses to improve perceived performance
3. **Batch Embeddings**: Generate multiple embeddings in a single request
4. **Model Selection**: Choose appropriately sized models for your hardware
5. **Connection Pooling**: Reuse the provider instance for multiple requests

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure Ollama is running: `ollama serve`
   - Check the base URL configuration

2. **Model Not Found**
   - List available models: `ollama list`
   - Install required model: `ollama pull model-name`

3. **Timeout Errors**
   - Increase timeout setting
   - Use smaller models or reduce max_tokens

4. **Memory Issues**
   - Use quantized models (Q4, Q8)
   - Reduce keep_alive time
   - Use smaller context windows

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This Ollama provider is part of the Plexus project and follows the same licensing terms.
