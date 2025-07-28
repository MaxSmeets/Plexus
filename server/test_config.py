"""
Quick test for settings loading.
"""

try:
    from api.core.config import settings
    print(f"✅ Settings loaded successfully!")
    print(f"   Project: {settings.PROJECT_NAME}")
    print(f"   Version: {settings.VERSION}")
    print(f"   Host: {settings.HOST}:{settings.PORT}")
    if hasattr(settings, 'MISTRAL_API_KEY'):
        print(f"   Mistral API Key: {'Set' if settings.MISTRAL_API_KEY else 'Not set'}")
    print("🎉 Configuration test passed!")
except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    import traceback
    traceback.print_exc()
