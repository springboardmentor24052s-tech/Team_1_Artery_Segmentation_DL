"""
StenoVision - Operational Tracing & Metrics Recording Middleware
================================================================
Injects X-Request-ID, instruments Prometheus request metrics,
and produces correlated structured JSON logs for all HTTP transactions.
"""

import time
import uuid
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION_SECONDS

logger = logging.getLogger("stenovision.access")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Correlates HTTP requests with unique IDs, Prometheus metrics, and structured logs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # 1. Resolve or generate unique Request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Normalize path for Prometheus endpoint grouping to avoid label cardinality explosion
        path = request.url.path
        if "/cases/" in path and len(path.split("/")) > 4:
            endpoint = "/api/v1/cases/{case_id}"
        elif "/images/" in path and len(path.split("/")) > 4:
            endpoint = "/api/v1/images/{image_id}"
        elif "/reports/" in path and len(path.split("/")) > 4:
            endpoint = "/api/v1/reports/{report_id}"
        elif "/models/" in path and len(path.split("/")) > 4:
            endpoint = "/api/v1/models/{model_id}"
        else:
            endpoint = path

        method = request.method
        client_ip = request.client.host if request.client else "unknown"

        # 2. Process Request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            duration = time.perf_counter() - start_time
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code=500).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)
            logger.error(
                f"Unhandled Exception processing {method} {path}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "method": method,
                    "path": path,
                    "status_code": 500,
                    "duration_ms": round(duration * 1000.0, 2),
                },
                exc_info=True,
            )
            raise exc

        # 3. Record Metrics and Execution Time
        duration = time.perf_counter() - start_time
        duration_ms = round(duration * 1000.0, 2)

        # Do not track internal healthcheck polling in standard Prometheus to keep histograms clean
        if endpoint not in ("/metrics", "/health"):
            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=endpoint, status_code=status_code
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

        # 4. Attach Request-ID Header to Response
        response.headers["X-Request-ID"] = request_id

        # 5. Emit Correlated Log
        log_level = logging.INFO if status_code < 400 else (logging.WARNING if status_code < 500 else logging.ERROR)
        logger.log(
            log_level,
            f"{method} {path} -> HTTP {status_code} ({duration_ms} ms)",
            extra={
                "request_id": request_id,
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
