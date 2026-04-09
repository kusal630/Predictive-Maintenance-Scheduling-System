"""
PMSS Run Script – starts the FastAPI backend server.
"""
import uvicorn
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("  PMSS – Predictive Maintenance Scheduling System")
    print("  Backend Server (FastAPI + LightGBM)")
    print(f"  URL: http://{settings.HOST}:{settings.PORT}")
    print(f"  Docs: http://localhost:{settings.PORT}/docs")
    print("=" * 60)
    print()

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
