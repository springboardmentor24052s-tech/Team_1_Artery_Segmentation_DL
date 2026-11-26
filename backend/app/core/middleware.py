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


def extract_client_ip(request: Request) -> str:
    """Resolves real client IP behind Nginx reverse proxy headers."""
    xff = request.headers.get("X-Forwarded-For", "").strip()
    if xff:
        return xff.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP", "").strip()
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def _extract_user_id_from_header(request: Request) -> int | None:
    """Best-effort extraction of authenticated user_id from Bearer JWT for access logs."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    if not token:
        return None
    try:
        from app.core.security import decode_access_token
        payload = decode_access_token(token)
        return int(payload["sub"])
    except Exception:
        return None


def _resolve_metric_endpoint(request: Request) -> str:
    """Returns matched FastAPI route template or '/unmatched' to avoid 404 cardinality explosion."""
    route = request.scope.get("route")
    route_path = getattr(route, "path", None) if route is not None else None
    return route_path if route_path else "/unmatched"


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Correlates HTTP requests with unique IDs, Prometheus metrics, and structured logs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # 1. Resolve or generate unique Request ID and real Client IP
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        path = request.url.path
        method = request.method
        client_ip = extract_client_ip(request)
        user_id = _extract_user_id_from_header(request)

        # 2. Process Request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            duration = time.perf_counter() - start_time
            endpoint = _resolve_metric_endpoint(request)
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status_code=500).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)
            logger.error(
                f"Unhandled Exception processing {method} {path}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "user_id": user_id,
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
        endpoint = _resolve_metric_endpoint(request)

        # Do not track internal healthcheck polling in standard Prometheus to keep histograms clean
        if path not in ("/metrics", "/health"):
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
                "user_id": user_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

        return response
