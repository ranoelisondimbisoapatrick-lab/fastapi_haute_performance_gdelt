"""run_api.py

Local entrypoint to run the FastAPI development server (no Docker).

Usage:
  poetry run python run_api.py

Notes:
- `reload=True` is for development only.
- For production, prefer:
  uvicorn app.main:app --host 0.0.0.0 --port 8000
  or gunicorn with UvicornWorker.
"""

import uvicorn


def main() -> None:
    """Start the development server."""
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
