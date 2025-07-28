"""
Development server startup script for the Plexus API.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Change to project root directory for imports
os.chdir(str(project_root))

try:
    import uvicorn
    from server.api.core.config import settings
    
    def main():
        """Start the development server."""
        print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
        print(f"Server will be available at: http://{settings.HOST}:{settings.PORT}")
        print(f"API Documentation: http://{settings.HOST}:{settings.PORT}{settings.API_V0_STR}/docs")
        print(f"Health Check: http://{settings.HOST}:{settings.PORT}{settings.API_V0_STR}/health")
        print("-" * 60)
        
        uvicorn.run(
            "server.api.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.RELOAD,
            log_level="info" if settings.DEBUG else "warning",
            access_log=True
        )

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
