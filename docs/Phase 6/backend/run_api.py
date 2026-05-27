"""Dev entry-point for the FastAPI backend (Phase 5a).

Run with:
    python run_api.py

For production:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
