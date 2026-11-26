from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import analysis, auth, case_images, cases, models, reports, users
from app.core.config import settings
from app.core.logging_config import LOG_DIR, setup_logging
from app.core.metrics import PIPELINE_READY, get_metrics_response, sync_active_cases_gauge
from app.core.middleware import ObservabilityMiddleware
from app.db.init_db import init_db
from app.db.session import SessionLocal
from sqlalchemy import text

# Initialize structured logging engine with HIPAA sanitization
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        try:
            sync_active_cases_gauge(db)
        except Exception as e:
            logger.warning(f"[METRICS] Failed initial active cases sync: {e}")
    try:
        from app.api.routes.analysis import get_pipeline
        get_pipeline()
        PIPELINE_READY.set(1)
    except Exception as e:
        PIPELINE_READY.set(0)
        logger.warning(f"[PIPELINE] Warmup warning: {e}")
    yield


app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0", lifespan=lifespan)

# Add observability, request-ID correlation, and metrics middleware
app.add_middleware(ObservabilityMiddleware)

# Enable CORS for Next.js web application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for uploads & generated XAI plots
backend_root = Path(__file__).resolve().parent.parent
static_dir = backend_root / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount multi-tier local medical storage
from app.services.storage import storage
storage.root.mkdir(parents=True, exist_ok=True)
app.mount("/static/storage", StaticFiles(directory=str(storage.root)), name="medical_storage")

# Mount Milestone 3 qualitative plots and live verification assets if present
m3_plots_dir = backend_root.parent / "milestone_3_results" / "qualitative_plots"
if m3_plots_dir.exists():
    app.mount("/static/qualitative_plots", StaticFiles(directory=str(m3_plots_dir)), name="qualitative_plots")

m3_live_dir = backend_root.parent / "milestone_3_results" / "live_verification"
if m3_live_dir.exists():
    app.mount("/static/live_verification", StaticFiles(directory=str(m3_live_dir)), name="live_verification")

# Core API Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users (admin)"])
app.include_router(cases.router, prefix="/api/v1/cases", tags=["Cases"])
app.include_router(case_images.router, prefix="/api/v1/cases", tags=["Case images"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Deep Learning Analysis"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Clinical Reports"])
app.include_router(models.router, prefix="/api/v1/models", tags=["Model Management & Versioning"])


@app.get("/health", tags=["Health"])
def health_check():
    import os
    import torch

    has_cuda = torch.cuda.is_available()
    device = torch.cuda.get_device_name(0) if has_cuda else "CPU Host"

    db_status = "ok"
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"
        logger.error(f"[HEALTH] PostgreSQL check failed: {exc}")

    log_dir_writable = os.access(LOG_DIR, os.W_OK)

    pipeline_ready = False
    try:
        from app.api.routes.analysis import _diagnostic_pipeline
        pipeline_ready = _diagnostic_pipeline is not None
    except Exception:
        pipeline_ready = False
    PIPELINE_READY.set(1 if pipeline_ready else 0)

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "project": "StenoVision Artery Analysis Engine",
        "dependencies": {
            "database": db_status,
            "log_dir_writable": log_dir_writable,
            "pipeline_ready": pipeline_ready,
        },
        "hardware_acceleration": {
            "mode": "CUDA_GPU" if has_cuda else "CPU",
            "device": device,
            "cuda_available": has_cuda,
        },
    }


@app.get("/metrics", tags=["Observability"])
def prometheus_metrics():
    """Exposes real-time Prometheus metrics for scrapers."""
    return get_metrics_response()

