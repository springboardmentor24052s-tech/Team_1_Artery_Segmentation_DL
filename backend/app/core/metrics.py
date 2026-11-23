"""
StenoVision - Prometheus Metrics Exporter & Operational Observability
=====================================================================
Exposes application-level, deep learning inference, and system metrics
in standard Prometheus exposition format on /metrics.
"""

import time
import torch
from typing import Optional
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY
)
from fastapi import Response

# 1. HTTP Traffic & Operational Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "stenovision_http_requests_total",
    "Total count of HTTP requests served by StenoVision backend",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "stenovision_request_duration_seconds",
    "HTTP request latency distribution across API endpoints",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# 2. Deep Learning Neural Pipeline Latencies
DL_INFERENCE_DURATION_SECONDS = Histogram(
    "stenovision_dl_inference_duration_seconds",
    "Deep learning inference execution latency across neural architectures",
    ["model_name"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0],
)

# 3. Clinical Application Gauges
ACTIVE_CASES_TOTAL = Gauge(
    "stenovision_active_cases_total",
    "Current volume of active coronary angiography cases in registry",
)

PROCESSED_ANGIOGRAMS_TOTAL = Counter(
    "stenovision_processed_angiograms_total",
    "Total volume of clinical angiograms processed through the AI pipeline",
    ["modality"],
)

# 4. System & Hardware Acceleration State
HARDWARE_INFO = Info(
    "stenovision_hardware_execution",
    "Underlying hardware acceleration mode and PyTorch compute device",
)

def initialize_hardware_info():
    """Records initial device execution environment into Prometheus Info metric."""
    has_cuda = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if has_cuda else "CPU Host"
    HARDWARE_INFO.info({
        "mode": "CUDA_GPU" if has_cuda else "CPU",
        "device": device_name,
        "cuda_version": torch.version.cuda or "none",
        "pytorch_version": torch.__version__,
    })

# Initialize hardware info on import
initialize_hardware_info()

def get_metrics_response() -> Response:
    """Generates standard Prometheus exposition payload."""
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
