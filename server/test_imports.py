"""
Test script to verify all imports work correctly.
"""

import sys
import traceback

def test_imports():
    """Test all critical imports."""
    try:
        print("✅ Testing basic imports...")
        import fastapi
        import uvicorn
        import pydantic
        from pydantic_settings import BaseSettings
        print("✅ All basic packages imported successfully!")
        
        print("\n✅ Testing API core imports...")
        from api.core.config import settings
        print(f"✅ Settings loaded: {settings.PROJECT_NAME} v{settings.VERSION}")
        
        print("\n✅ Testing API main import...")
        from api.main import app
        print("✅ FastAPI app created successfully!")
        
        print("\n✅ Testing agent import...")
        try:
            from agents.shopping_list_agent import shopping_list_agent
            print("✅ Shopping list agent imported successfully!")
        except ImportError as e:
            print(f"⚠️  Shopping list agent import failed: {e}")
            print("   This is expected if MISTRAL_API_KEY is not set")
        
        print("\n🎉 All critical imports successful! API should work.")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        print("\n📋 Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
