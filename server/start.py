"""
Simple API server launcher for Plexus.
Run this from the project root directory.
"""

import sys
import os

if __name__ == "__main__":
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        import uvicorn
        
        print("🚀 Starting Plexus API Server...")
        print("📝 API Documentation will be available at: http://127.0.0.1:8000/api/v0/docs")
        print("🏥 Health Check: http://127.0.0.1:8000/api/v0/health")
        print("=" * 60)
        
        uvicorn.run(
            "server.api.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("❌ Required packages not installed.")
        print("Please install them with: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("Make sure you're running this from the project root directory.")
