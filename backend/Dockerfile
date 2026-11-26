# ==============================================================================
# StenoVision Backend Dockerfile (FastAPI + PyTorch + ReportLab)
# Production Container Specification (Milestone 4 Section 17)
# ==============================================================================

FROM python:3.11-slim as base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install minimal OS dependencies for OpenCV, Pillow and healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app /app/app

# Create persistent storage and logging directories with proper permissions
RUN mkdir -p /app/static/reports /app/static/uploads /app/static/xai /app/storage/raw /app/storage/masks /app/storage/xai /app/storage/reports /app/logs

# Create non-root user for container security
RUN adduser --disabled-password --gecos "" stenovision && \
    chown -R stenovision:stenovision /app

USER stenovision

# Expose FastAPI REST service port
EXPOSE 8000

# Health check to ensure API availability
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn ASGI server (single worker to fit 1 GB EC2 RAM & unify Prometheus metrics)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
