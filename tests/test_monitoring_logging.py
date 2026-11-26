"""
Automated verification tests for StenoVision monitoring, Prometheus metrics,
Grafana provisioning, Docker log rotation, and HIPAA-sanitized JSON logging.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import yaml
from fastapi.testclient import TestClient

REVIEW_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REVIEW_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.logging_config import MAIN_LOG_FILE, ERROR_LOG_FILE, sanitize_phi  # noqa: E402
from app.core.metrics import (  # noqa: E402
    ACTIVE_CASES_TOTAL,
    DL_INFERENCE_DURATION_SECONDS,
    PIPELINE_READY,
    PROCESSED_ANGIOGRAMS_TOTAL,
)
from app.main import app  # noqa: E402


def test_phi_redaction_sanitizer():
    """Verify HIPAA Safe Harbor identifiers are redacted before log persistence."""
    raw = (
        "Patient John Doe mrn=MRN-99482 email=patient@hospital.org "
        "phone=555-867-5309 ssn=123-45-6789 date=1984-07-19"
    )
    scrubbed = sanitize_phi(raw)
    assert "123-45-6789" not in scrubbed and "[REDACTED_SSN]" in scrubbed
    assert "555-867-5309" not in scrubbed and "[REDACTED_PHONE]" in scrubbed
    assert "patient@hospital.org" not in scrubbed and "[REDACTED_EMAIL]" in scrubbed
    assert "MRN-99482" not in scrubbed and "[REDACTED_MRN]" in scrubbed
    assert "1984-07-19" not in scrubbed and "[REDACTED_DATE]" in scrubbed


def test_monitoring_configs_and_dashboards_valid():
    """Validate Prometheus config, alert rules, Grafana datasource UID, and Compose log limits."""
    prom_cfg = yaml.safe_load((REVIEW_ROOT / "monitoring" / "prometheus" / "prometheus.yml").read_text(encoding="utf-8"))
    assert "/etc/prometheus/alerts.yml" in prom_cfg.get("rule_files", [])

    alerts_cfg = yaml.safe_load((REVIEW_ROOT / "monitoring" / "prometheus" / "alerts.yml").read_text(encoding="utf-8"))
    rule_names = {r["alert"] for g in alerts_cfg["groups"] for r in g["rules"]}
    assert {
        "StenoVisionBackendDown",
        "StenoVisionHigh5xxErrorRate",
        "StenoVisionHighRequestLatencyP95",
        "StenoVisionSlowDLInferenceP95",
    }.issubset(rule_names)

    ds_cfg = yaml.safe_load(
        (REVIEW_ROOT / "monitoring" / "grafana" / "provisioning" / "datasources" / "prometheus.yml").read_text(
            encoding="utf-8"
        )
    )
    assert ds_cfg["datasources"][0]["uid"] == "Prometheus"

    dash = json.loads(
        (REVIEW_ROOT / "monitoring" / "grafana" / "dashboards" / "stenovision_overview.json").read_text(encoding="utf-8")
    )
    panel_titles = {p["title"] for p in dash["panels"] if p.get("type") != "row"}
    assert "DL Pipeline Readiness" in panel_titles
    assert "Processed Angiograms by Modality" in panel_titles
    assert "HTTP Traffic & Error Rate by Status Class (2xx / 4xx / 5xx)" in panel_titles

    compose_cfg = yaml.safe_load((REVIEW_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    for svc_name, svc in compose_cfg["services"].items():
        log_cfg = svc.get("logging", {})
        assert log_cfg.get("driver") == "json-file", f"{svc_name} missing json-file log driver"
        assert log_cfg.get("options", {}).get("max-size") == "10m", f"{svc_name} missing max-size"
        assert log_cfg.get("options", {}).get("max-file") == "3", f"{svc_name} missing max-file"


def test_metrics_cardinality_health_and_json_logs(tmp_path):
    """Verify /health, /metrics, 404 cardinality bounding, X-Request-ID, and structured logs."""
    mock_db = MagicMock()
    mock_db.execute.return_value = 1

    with TestClient(app) as client:
        # 1. Deep health check payload
        r_health = client.get("/health")
        assert r_health.status_code == 200
        body = r_health.json()
        assert "dependencies" in body
        assert "log_dir_writable" in body["dependencies"]
        assert "pipeline_ready" in body["dependencies"]
        assert "X-Request-ID" in r_health.headers

        # 2. Scanner 404 should aggregate under endpoint="/unmatched" (zero cardinality explosion)
        scanner_path = "/api/.env.probe.test"
        r_404 = client.get(scanner_path, headers={"X-Request-ID": "req-probe-404"})
        assert r_404.status_code == 404
        assert r_404.headers.get("X-Request-ID") == "req-probe-404"

        # 3. Record synthetic DL + active cases metrics to confirm exposition
        ACTIVE_CASES_TOTAL.set(7)
        PIPELINE_READY.set(1)
        DL_INFERENCE_DURATION_SECONDS.labels(model_name="StenoVision-Pipeline").observe(0.042)
        PROCESSED_ANGIOGRAMS_TOTAL.labels(modality="2D_XCA").inc()

        r_metrics = client.get("/metrics")
        assert r_metrics.status_code == 200
        m_txt = r_metrics.text
        assert 'endpoint="/unmatched"' in m_txt
        assert scanner_path not in m_txt
        assert "stenovision_active_cases_total 7.0" in m_txt
        assert "stenovision_pipeline_ready 1.0" in m_txt
        assert 'stenovision_dl_inference_duration_seconds_count{model_name="StenoVision-Pipeline"}' in m_txt
        assert 'stenovision_processed_angiograms_total{modality="2D_XCA"}' in m_txt

        # 4. Verify structured JSON log records exist with X-Request-ID correlation
        assert MAIN_LOG_FILE.exists()
        assert ERROR_LOG_FILE.exists()
        recent_lines = [line for line in MAIN_LOG_FILE.read_text(encoding="utf-8").splitlines()[-20:] if line.strip()]
        parsed = [json.loads(line) for line in recent_lines]
        assert any(entry.get("request_id") == "req-probe-404" for entry in parsed)


def test_login_audit_real_ip_and_rbac():
    """Verify per-user login audit logging, X-Forwarded-For IP capture, Prometheus counter, and RBAC."""
    from app.api.routes.auth import mask_email

    assert mask_email("sathiya@stenovision.ai") == "s***@stenovision.ai"

    with TestClient(app) as client:
        # Failed login attempt via reverse proxy IP
        r_fail = client.post(
            "/api/v1/auth/login",
            data={"username": "sathiya@stenovision.ai", "password": "wrong-password"},
            headers={"X-Forwarded-For": "203.0.113.42, 172.18.0.6", "User-Agent": "AuditTestClient/1.0"},
        )
        assert r_fail.status_code == 401

        # Successful developer login
        r_ok = client.post(
            "/api/v1/auth/login",
            data={"username": "sathiya@stenovision.ai", "password": "sathiyapassword123"},
            headers={"X-Forwarded-For": "203.0.113.42", "User-Agent": "AuditTestClient/1.0", "X-Request-ID": "audit-req-1"},
        )
        assert r_ok.status_code == 200
        dev_token = r_ok.json()["access_token"]

        # Developer (Sathiya) can inspect login audit trail
        r_audit = client.get(
            "/api/v1/users/audit",
            headers={"Authorization": f"Bearer {dev_token}", "X-Real-IP": "203.0.113.42"},
        )
        assert r_audit.status_code == 200
        data = r_audit.json()
        assert data["total_events"] >= 2
        assert any(
            ev["client_ip"] == "203.0.113.42"
            and ev["outcome"] == "success"
            and ev["user_role"] == "Developer"
            and ev["request_id"] == "audit-req-1"
            for ev in data["recent_logins"]
        )
        assert any(
            ev["outcome"] == "invalid_credentials" and ev["attempted_email_masked"] == "s***@stenovision.ai"
            for ev in data["recent_logins"]
        )
        assert any(u["email"] == "sathiya@stenovision.ai" and u["last_login_at"] is not None for u in data["active_users"])

        # Non-admin user (Medical Researcher) is blocked (403) from audit endpoint
        r_res = client.post(
            "/api/v1/auth/login",
            data={"username": "d.chen@stenovision.org", "password": "chenpassword123"},
        )
        assert r_res.status_code == 200
        res_token = r_res.json()["access_token"]
        r_forbidden = client.get("/api/v1/users/audit", headers={"Authorization": f"Bearer {res_token}"})
        assert r_forbidden.status_code == 403

        # Prometheus metrics include stenovision_auth_logins_total
        r_metrics = client.get("/metrics")
        assert "stenovision_auth_logins_total" in r_metrics.text

        # Backend JSON log includes real client_ip and user_id on authenticated request
        recent = [json.loads(l) for l in MAIN_LOG_FILE.read_text(encoding="utf-8").splitlines()[-25:] if l.strip()]
        assert any(e.get("path") == "/api/v1/users/audit" and e.get("user_id") is not None and e.get("client_ip") == "203.0.113.42" for e in recent)
