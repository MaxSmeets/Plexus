# Model Providers & Integration

This directory contains integrations with various LLM providers and local model runners.

## Contents:
- Local model runners (Ollama, LM Studio integration)
- API clients for cloud models (OpenAI, Anthropic, etc.)
- Model switching/routing logic
- Prompt templating system
- Response parsing and validation utilities
- Model configuration management
- Model performance metrics
- Caching mechanisms
- Fallback strategies

## Available Providers

### Ollama Provider ✅ IMPLEMENTED
**Location**: `ollama/`

Full-featured integration with Ollama for running local language models.

**Features**:
- Chat completions with message history
- Text generation and completions
- Embedding generation
- Streaming responses
- Multimodal support (text + images)
- Model management (list, pull, delete)
- Health monitoring
- Robust error handling with retries

**Quick Start**:
```python
from model_providers.ollama import OllamaProvider, OllamaConfig

# Initialize provider
config = OllamaConfig(base_url="http://localhost:11434")
provider = OllamaProvider(config.to_dict())

# Use the provider
await provider.initialize()
models = await provider.list_models()
```

**Requirements**:
- Ollama installed and running
- At least one model pulled (e.g., `ollama pull llama3.2`)
- Python dependencies: `aiohttp>=3.8.0`

**Supported Models**:
- Text Generation: llama3.2, mistral, codellama, etc.
- Embeddings: all-minilm, nomic-embed-text, etc.
- Multimodal: llava, bakllava, etc.

## Planned Providers

### OpenAI Provider 🚧 PLANNED
- GPT-4, GPT-3.5 Turbo
- DALL-E image generation
- Whisper speech-to-text
- Text embeddings

### Anthropic Provider 🚧 PLANNED
- Claude 3.5 Sonnet, Claude 3 Haiku
- Message API integration
- Tool use capabilities

### LM Studio Provider 🚧 PLANNED
- Local model serving
- OpenAI-compatible API
- Custom model support

### Hugging Face Provider 🚧 PLANNED
- Transformers integration
- Pipeline abstractions
- Local and remote models

## Architecture

### Base Provider Interface
All providers implement the `BaseModelProvider` abstract class:

```python
class BaseModelProvider(ABC):
    async def initialize(self) -> bool
    async def list_models(self) -> List[str]
    async def generate_chat(messages, model, parameters) -> Union[ModelResponse, AsyncGenerator]
    async def generate_completion(prompt, model, parameters) -> Union[ModelResponse, AsyncGenerator]
    async def generate_embeddings(texts, model) -> List[List[float]]
    async def health_check(self) -> Dict[str, Any]
```

### Common Data Types
- `ChatMessage`: Represents messages in conversations
- `ModelParameters`: Configuration for generation (temperature, top_p, etc.)
- `ModelResponse`: Complete response from model
- `StreamChunk`: Individual chunk in streaming response

### Provider Factory
```python
from model_providers import create_provider, get_available_providers

# List available providers
providers = get_available_providers()  # ["ollama"]

# Create provider instance
provider = create_provider("ollama", config)
```

## Configuration

Each provider supports configuration through:
1. Environment variables
2. Configuration files (JSON/YAML)
3. Direct configuration objects

Example configuration hierarchy:
```
Environment Variables → Config File → Default Values
```

## Error Handling

All providers use consistent error handling:
- `ProviderError`: Base exception for provider issues
- `ModelNotFoundError`: Requested model not available
- `ConnectionError`: Network/connection issues
- `ConfigurationError`: Invalid configuration
- `RateLimitError`: API rate limits exceeded

## Testing

Each provider includes:
- Unit tests for core functionality
- Integration tests with real services
- Performance benchmarks
- Health check utilities

Run provider tests:
```bash
# Test specific provider
python -m model_providers.ollama.test_basic

# Test all providers
python -m model_providers.test_all
```

## Contributing

To add a new provider:

1. Create provider directory: `providers/your_provider/`
2. Implement `BaseModelProvider` interface
3. Add configuration class
4. Include utility functions
5. Write comprehensive tests
6. Add documentation and examples
7. Update main `__init__.py` to register provider

See `ollama/` for a complete reference implementation.
