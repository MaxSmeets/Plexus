#!/usr/bin/env python3
"""
Setup script for the Ollama model provider.

This script installs the required dependencies and performs basic setup.
"""

import subprocess
import sys
import os
from pathlib import Path


def install_requirements():
    """Install required packages."""
    print("Installing required dependencies...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"Requirements file not found: {requirements_file}")
        return False
    
    try:
        # Install using pip
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], capture_output=True, text=True, check=True)
        
        print("✓ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_ollama_installation():
    """Check if Ollama is installed and accessible."""
    print("Checking Ollama installation...")
    
    try:
        result = subprocess.run(["ollama", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✓ Ollama found: {result.stdout.strip()}")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Ollama not found in PATH")
        print("  Please install Ollama from https://ollama.com")
        return False


def check_ollama_service():
    """Check if Ollama service is running."""
    print("Checking Ollama service...")
    
    try:
        # Try to connect to Ollama API
        import urllib.request
        import json
        
        try:
            with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read())
                    models = data.get("models", [])
                    print(f"✓ Ollama service is running with {len(models)} models")
                    return True
                else:
                    print(f"✗ Ollama service responded with status {response.status}")
                    return False
                    
        except urllib.error.URLError:
            print("✗ Cannot connect to Ollama service at http://localhost:11434")
            print("  Please start Ollama service with: ollama serve")
            return False
            
    except ImportError:
        print("⚠️  Cannot check Ollama service (urllib not available)")
        return None


def suggest_models():
    """Suggest models to install."""
    print("\\nRecommended models to install:")
    print("  For chat/text generation:")
    print("    ollama pull llama3.2:latest")
    print("    ollama pull mistral:latest")
    print("  ")
    print("  For embeddings:")
    print("    ollama pull all-minilm:latest")
    print("  ")
    print("  For multimodal (text + images):")
    print("    ollama pull llava:latest")
    print("  ")
    print("  List installed models:")
    print("    ollama list")


def run_basic_test():
    """Run basic connectivity test."""
    print("\\nRunning basic connectivity test...")
    
    try:
        # Import and run the test
        from .test_basic import test_connection
        import asyncio
        
        async def run_test():
            return await test_connection()
        
        success = asyncio.run(run_test())
        
        if success:
            print("✓ Basic test passed - Ollama provider is ready!")
        else:
            print("✗ Basic test failed - please check your setup")
            
        return success
        
    except ImportError as e:
        print(f"⚠️  Cannot run test: {e}")
        return None
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False


def main():
    """Main setup function."""
    print("Ollama Model Provider Setup")
    print("=" * 40)
    
    success_count = 0
    total_checks = 0
    
    # Install dependencies
    total_checks += 1
    if install_requirements():
        success_count += 1
    
    # Check Ollama installation
    total_checks += 1
    if check_ollama_installation():
        success_count += 1
    
    # Check Ollama service
    service_result = check_ollama_service()
    if service_result is not None:
        total_checks += 1
        if service_result:
            success_count += 1
    
    # Summary
    print("\\n" + "=" * 40)
    print("Setup Summary:")
    print("=" * 40)
    print(f"Checks passed: {success_count}/{total_checks}")
    
    if success_count == total_checks:
        print("🎉 Setup completed successfully!")
        
        # Run basic test if everything looks good
        test_result = run_basic_test()
        if test_result:
            print("\\n✅ Ollama provider is fully functional!")
        else:
            print("\\n⚠️  Setup complete but test failed - check your models")
            suggest_models()
    else:
        print("⚠️  Setup incomplete - please address the issues above")
        suggest_models()
    
    return success_count == total_checks


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n\\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n\\nUnexpected error during setup: {e}")
        sys.exit(1)
