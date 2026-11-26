"""
StenoVision - Structured JSON Logging & HIPAA Compliance Sanitizer
==================================================================
Outputs standardized ISO-8601 JSON log streams with X-Request-ID correlation,
automatic Protected Health Information (PHI) redaction, and rotating file handlers.
"""

import os
import re
import sys
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

# Resolve project log directory
CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parent.parent.parent
LOG_DIR = BACKEND_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

MAIN_LOG_FILE = LOG_DIR / "stenovision.log"
ERROR_LOG_FILE = LOG_DIR / "stenovision_error.log"

# HIPAA Safe Harbor Direct Identifier Patterns for Automatic Redaction
PHI_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[REDACTED_PHONE]"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?i)\b(?:mrn|patient_id|pat_id)[-:\s=]+['\"]?([A-Za-z0-9_-]{4,15})['\"]?"), r"mrn=[REDACTED_MRN]"),
    (re.compile(r"(?i)\b(?:patient_name|patientName|full_name)[-:\s=]+['\"]?([A-Za-z\s]{3,30})['\"]?"), r"patient_name=[REDACTED_NAME]"),
    (re.compile(r"\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b"), "[REDACTED_DATE]"),
]

def sanitize_phi(text: str) -> str:
    """Scrubs direct patient identifiers from text to maintain HIPAA Safe Harbor compliance."""
    if not isinstance(text, str):
        text = str(text)
    for pattern, replacement in PHI_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_phi(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include request & user tracing context if attached
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "client_ip"):
            log_entry["client_ip"] = record.client_ip
        if hasattr(record, "user_id") and record.user_id is not None:
            log_entry["user_id"] = record.user_id
        if hasattr(record, "user_role") and record.user_role is not None:
            log_entry["user_role"] = record.user_role
        if hasattr(record, "auth_outcome") and record.auth_outcome is not None:
            log_entry["auth_outcome"] = record.auth_outcome
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "path"):
            log_entry["path"] = sanitize_phi(record.path)
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configures root and application loggers with rotating files and JSON output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if re-initialized
    if root_logger.handlers:
        root_logger.handlers.clear()

    json_formatter = StructuredJsonFormatter()

    # 1. Rotating File Handler - All Logs (10 MB x 5 backups = max 50 MB)
    file_handler = RotatingFileHandler(
        str(MAIN_LOG_FILE),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)

    # 2. Rotating File Handler - Errors Only (10 MB x 5 backups)
    error_file_handler = RotatingFileHandler(
        str(ERROR_LOG_FILE),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.WARNING)
    error_file_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_file_handler)

    # 3. Console Stream Handler (stdout for container log drivers)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(json_formatter)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger("stenovision")
    logger.info("Structured JSON logging initialized with HIPAA sanitization and rotating file storage.")
    return logger
