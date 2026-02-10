"""app.core.metrics

Prometheus metrics for FastAPI.

Exposed endpoint:
- GET /metrics

Metrics collected:
- http_requests_total{method, path, status}
- http_request_latency_seconds{method, path}

Cardinality note:
- Using raw path as a label may create high-cardinality metrics if you have dynamic paths.
  For POC it's acceptable. In production, prefer route templates (e.g., /items/{id}).
"""

from __future__ import annotations

import time

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQ_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQ_LAT = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency",
    ["method", "path"],
)


async def metrics_middleware(request: Request, call_next):
    """Measure request duration and increment Prometheus counters."""
    start = time.perf_counter()
    response = await call_next(request)
    dur = time.perf_counter() - start

    path = request.url.path
    REQ_LAT.labels(request.method, path).observe(dur)
    REQ_COUNT.labels(request.method, path, str(response.status_code)).inc()

    return response


def metrics_endpoint() -> Response:
    """Return Prometheus scrape payload."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
