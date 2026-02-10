"""Run the FastAPI server locally (no Docker).

Usage:
  poetry run python run_api.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
