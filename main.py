#!/usr/bin/env python3
"""
Plexus Ollama Streaming Demo

A script that demonstrates how to use the Ollama provider to submit a prompt
and receive a streamed response in the terminal.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from model_providers.ollama.provider import OllamaProvider
from model_providers.ollama.config import OllamaConfig
from model_providers.base_provider import ChatMessage, MessageRole, ModelParameters


async def check_ollama_connection(provider: OllamaProvider) -> bool:
    """Check if Ollama is available and list models."""
    try:
        await provider.initialize()
        if not provider.is_available:
            print("❌ Ollama service is not available")
            return False
        
        models = await provider.list_models()
        if not models:
            print("❌ No models available in Ollama")
            return False
        
        print(f"✅ Ollama connected! Available models: {', '.join(models)}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {e}")
        return False


async def stream_chat_response(provider: OllamaProvider, model: str, user_input: str):
    """Stream a chat response from Ollama."""
    try:
        # Create chat message
        messages = [ChatMessage(role=MessageRole.USER, content=user_input)]
        
        # Set up streaming parameters
        parameters = ModelParameters(
            temperature=0.8,
            stream=True,
            max_tokens=500
        )
        
        print(f"\n🤖 Model: {model}")
        print(f"💬 User: {user_input}")
        print("🔄 Assistant: ", end="", flush=True)
        
        # Get streaming response
        response_stream = await provider.generate_chat(
            messages=messages,
            model=model,
            parameters=parameters
        )
        
        full_response = ""
        async for chunk in response_stream:
            if chunk.content:
                print(chunk.content, end="", flush=True)
                full_response += chunk.content
            
            if chunk.is_final:
                print("\n✨ Response complete!")
                break
        
        return full_response
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Stream interrupted by user")
        return None
    except Exception as e:
        print(f"\n❌ Error during streaming: {e}")
        return None


async def interactive_chat(provider: OllamaProvider, model: str):
    """Run an interactive chat session."""
    print(f"\n🚀 Starting interactive chat with {model}")
    print("💡 Type 'quit' to exit, 'clear' to clear history")
    print("-" * 50)
    
    messages = []
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'clear':
                messages.clear()
                print("🗑️ Chat history cleared!")
                continue
            elif not user_input:
                continue
            
            # Add user message to history
            messages.append(ChatMessage(role=MessageRole.USER, content=user_input))
            
            # Stream response
            print("🤖 Assistant: ", end="", flush=True)
            
            parameters = ModelParameters(
                temperature=0.8,
                stream=True,
                max_tokens=500
            )
            
            response_stream = await provider.generate_chat(
                messages=messages,
                model=model,
                parameters=parameters
            )
            
            assistant_response = ""
            async for chunk in response_stream:
                if chunk.content:
                    print(chunk.content, end="", flush=True)
                    assistant_response += chunk.content
                
                if chunk.is_final:
                    break
            
            print()  # New line after response
            
            # Add assistant response to history
            if assistant_response:
                messages.append(ChatMessage(
                    role=MessageRole.ASSISTANT, 
                    content=assistant_response
                ))
            
        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    """Main function to run the Ollama streaming demo."""
    print("🎯 Plexus Ollama Streaming Demo")
    print("=" * 40)
    
    # Load configuration
    config = OllamaConfig.from_env()
    print(f"🔗 Connecting to Ollama at: {config.base_url}")
    
    # Initialize provider
    config_dict = {
        "base_url": config.base_url,
        "timeout": config.timeout,
        "keep_alive": config.keep_alive,
        "max_retries": config.max_retries,
        "retry_delay": config.retry_delay,
        "verify_ssl": config.verify_ssl,
        "custom_headers": config.custom_headers
    }
    provider = OllamaProvider(config_dict)
    
    try:
        # Check connection and get models
        if not await check_ollama_connection(provider):
            return 1
        
        models = await provider.list_models()
        
        # Select model
        print(f"\n📋 Available models ({len(models)}):")
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model}")
        
        while True:
            try:
                choice = input(f"\n🎯 Select model (1-{len(models)}) or enter model name: ").strip()
                
                if choice.isdigit() and 1 <= int(choice) <= len(models):
                    selected_model = models[int(choice) - 1]
                    break
                elif choice in models:
                    selected_model = choice
                    break
                else:
                    print(f"❌ Invalid choice. Please select 1-{len(models)} or enter a valid model name.")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                return 0
        
        print(f"\n✅ Selected model: {selected_model}")
        
        # Choose mode
        print("\n📝 Choose interaction mode:")
        print("  1. Single prompt")
        print("  2. Interactive chat")
        
        while True:
            try:
                mode = input("🎯 Select mode (1 or 2): ").strip()
                if mode in ['1', '2']:
                    break
                print("❌ Please enter 1 or 2")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                return 0
        
        if mode == '1':
            # Single prompt mode
            user_input = input("\n💭 Enter your prompt: ").strip()
            if user_input:
                await stream_chat_response(provider, selected_model, user_input)
        else:
            # Interactive chat mode
            await interactive_chat(provider, selected_model)
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    finally:
        await provider.close()
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n👋 Program interrupted. Goodbye!")
        sys.exit(0)
