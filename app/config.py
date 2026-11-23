"""Central configuration. Every value can be overridden with an environment variable."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", BASE_DIR / "models"))
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", BASE_DIR / "storage"))
UPLOAD_DIR = STORAGE_DIR / "uploads"
RESULTS_DIR = STORAGE_DIR / "results"
FRONTEND_DIR = BASE_DIR / "frontend"

for _d in (MODELS_DIR, UPLOAD_DIR, RESULTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# SQLite by default (zero setup); docker-compose switches this to PostgreSQL.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{STORAGE_DIR / 'artery.db'}")

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production-please-32+chars")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "480"))

# Default admin created on first start (change the password after logging in).
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@artery.ai")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")

IMAGE_SIZE = 512
MAX_UPLOAD_MB = 50

# Severity thresholds (% diameter reduction), aligned with CAD-RADS 2.0 grading.
# CAD-RADS: 0 none, 1-24 minimal, 25-49 mild, 50-69 moderate, 70-99 severe, 100 occlusion.
# "Critical" here groups sub-total/total occlusion (>= 90 %). Configurable on purpose:
# the project brief requires thresholds to follow the chosen clinical reference standard.
SEVERITY_THRESHOLDS = [
    (25.0, "Normal"),      # < 25 %  -> minimal / no significant narrowing
    (50.0, "Mild"),        # 25-49 %
    (70.0, "Moderate"),    # 50-69 %
    (90.0, "Severe"),      # 70-89 %
    (101.0, "Critical"),   # >= 90 %
]

LOW_CONFIDENCE = float(os.getenv("LOW_CONFIDENCE", "0.5"))
DEVICE = os.getenv("DEVICE", "auto")  # auto | cpu | cuda | mps

# --- Microservices -------------------------------------------------------------------------------------------
# Empty = run the AI pipeline inside the API process (development). Set to the inference service URL in Docker.
INFERENCE_URL = os.getenv("INFERENCE_URL", "")
# Shared secret for service-to-service calls and the Prometheus endpoint. Change it in production.
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN", "dev-internal-token-change-me")

# --- Security -------------------------------------------------------------------------------------------------
# Fernet key for encryption at rest. Leave empty to auto-generate storage/secret.key (keep that file safe).
DATA_ENCRYPTION_KEY = os.getenv("DATA_ENCRYPTION_KEY", "")
LOGIN_RATE_LIMIT_PER_MIN = int(os.getenv("LOGIN_RATE_LIMIT_PER_MIN", "10"))
API_RATE_LIMIT_PER_MIN = int(os.getenv("API_RATE_LIMIT_PER_MIN", "600"))

# --- Monitoring & notifications -------------------------------------------------------------------------------
LOG_DIR = Path(os.getenv("LOG_DIR", BASE_DIR / "logs"))
SMTP_HOST = os.getenv("SMTP_HOST", "")          # e.g. smtp.office365.com; empty = e-mail alerts disabled
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "arterix-alerts@localhost")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")      # recipient for high and critical alerts
