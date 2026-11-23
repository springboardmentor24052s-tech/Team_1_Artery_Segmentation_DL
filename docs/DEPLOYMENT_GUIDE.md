# StenoVision Production Containerization, Deployment & Observability Guide

This guide provides exhaustive production deployment blueprints, Docker container orchestration, AWS Free Tier EC2 provisioning, and enterprise observability configuration for **StenoVision**.

---

## 1. Architecture Overview

StenoVision deploys as a cohesive 6-service microservice stack orchestrating reverse proxying, deep learning inference, modern clinical workstation frontends, relational case persistence, metrics collection, and real-time visual telemetry:

```
                          Internet / Clinical Intranet
                                       │
                                       ▼
                       ┌──────────────────────────────┐
                       │   Nginx Reverse Proxy (:80)  │
                       └──────────────┬───────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              │ /api/, /docs, /health, /metrics                │ / (Web App)
              ▼                                               ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│  FastAPI DL Engine (:8000)   │              │   Next.js Workstation (:3000)│
│  - PyTorch (CUDA / CPU)      │              │   - Tailwind CSS / Lucide    │
│  - Attention U-Net & YOLOv8  │              │   - DICOM / Angiogram Viewer │
│  - Structured JSON Logging   │              └──────────────────────────────┘
│  - HIPAA Safe Harbor Masking │
└──────────────┬───────────────┘
               │
       ┌───────┴───────────────────────┬───────────────────────────────┐
       ▼                               ▼                               ▼
┌──────────────┐              ┌───────────────────┐        ┌───────────────────┐
│ PostgreSQL 15│              │ Prometheus (:9090)│───────▶│  Grafana (:3001)  │
│ Port: 5432   │              │ Scrape /metrics   │        │ Dashboards & KPIs │
└──────────────┘              └───────────────────┘        └───────────────────┘
```

### Complete Service Matrix
| Service | Container Port | Host Port | Technology | Purpose | Healthcheck |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`nginx`** | `80` | `80` | Nginx 1.25 Alpine | Reverse proxy gateway, SSL/TLS termination, rate limiting | HTTP GET `/health` |
| **`backend`** | `8000` | `8000` | FastAPI / Python 3.11 | Coronary segmentation, stenosis detection, QCA, Grad-CAM, HIPAA logging | HTTP GET `/health` |
| **`frontend`** | `3000` | `3000` | Next.js 15 / React 19 | Clinical Workstation, interactive ROI viewer, report export | HTTP GET `/` |
| **`postgres`**| `5432` | `5432` | PostgreSQL 15 Alpine | HIPAA-compliant relational audit trail, case metadata, user roles | `pg_isready` |
| **`prometheus`**| `9090` | `9090` | Prometheus v2.45.0 | High-resolution time-series metrics collector (10s scrape interval) | TCP `9090` |
| **`grafana`** | `3000` | `3001` | Grafana Enterprise | Pre-provisioned clinical telemetry & system health dashboards | HTTP GET `/api/health` |

---

## 2. Deployment Options

### Option A: Local Docker Compose Orchestration (Production Ready)
Spin up the complete 6-container stack with one command:
```bash
docker compose up -d --build
```

To view real-time logs across all services:
```bash
docker compose logs -f
```

To safely bring down the stack while preserving data volumes:
```bash
docker compose down
```

---

### Option B: AWS Free Tier EC2 Cloud Deployment
StenoVision includes automated provisioning engineered specifically for the **AWS Free Tier** (`t2.micro` or `t3.micro` instances: 1 vCPU, 1 GB RAM, 30 GB EBS).

#### Memory Optimization (The 3 GB Swap Strategy)
Because deep learning models and Next.js builds can exceed 1 GB RAM, the automated script creates a 3 GB Linux swap partition on the free 30 GB EBS volume. This expands the effective virtual memory to **4 GB RAM**, completely preventing Out-Of-Memory (`OOMKilled`) termination while staying 100% within the AWS Free Tier.

#### Automated Cloud Provisioning Steps:
1. Launch an AWS EC2 instance:
   - **AMI**: Ubuntu Server 22.04 LTS or 24.04 LTS (64-bit x86)
   - **Instance Type**: `t2.micro` or `t3.micro` (Free Tier Eligible)
   - **Storage**: 30 GB gp3 EBS Volume (Free Tier Eligible)
   - **Security Group Inbound Rules**:
     - `SSH (22)`: Your IP
     - `HTTP (80)`: `0.0.0.0/0` (Unified Public Portal)
     - `Custom TCP (3001)`: `0.0.0.0/0` (Grafana Telemetry)
     - `Custom TCP (9090)`: Your IP / VPN (Prometheus Admin)
2. Connect to your instance via SSH:
   ```bash
   ssh -i your-key.pem ubuntu@<your-ec2-ip>
   ```
3. Clone or copy your project repository to the instance.
4. Execute the automated setup script with `sudo`:
   ```bash
   cd review
   sudo bash deploy/aws_ec2_setup.sh
   ```
5. The script automatically:
   - Configures 3 GB swap space and optimizes kernel swappiness (`vm.swappiness=20`).
   - Installs Docker Engine and Docker Compose V2.
   - Configures the UFW firewall.
   - Compiles and launches all 6 containers with self-healing restart policies.

---

### Option C: Native Local Launch (Windows PowerShell)
If Docker Desktop is not installed or when performing rapid local development:
```powershell
.\run_stenovision.ps1
```
This launcher:
1. Validates Python 3.10+ and Node.js 18+ environments.
2. Checks CUDA GPU availability with automatic CPU fallback.
3. Initializes rotating structured JSON log handlers in `backend/logs/`.
4. Boots the FastAPI backend on `http://127.0.0.1:8000`.
5. Pre-warms deep learning pipelines for sub-second inference.
6. Boots the Next.js frontend on `http://localhost:3000`.

---

## 3. Monitoring & Observability Setup

StenoVision features enterprise observability out of the box.

### Prometheus Metrics (`http://<host>:9090`)
The backend exposes native Prometheus metrics at `GET /metrics`. Key metrics tracked:
- `stenovision_http_requests_total`: Total HTTP requests partitioned by `method`, `endpoint`, and `status`.
- `stenovision_http_request_duration_seconds`: High-resolution request latency histogram.
- `stenovision_dl_inference_duration_seconds`: Model execution latency for U-Net, YOLO, and QCA calipers.
- `stenovision_active_cases_total`: Gauge tracking concurrent cases being processed.
- `stenovision_hardware_info`: Hardware telemetry (`mode="CUDA_GPU"` or `"CPU"`, device name, CUDA version).

### Grafana Clinical Dashboards (`http://<host>:3001`)
Grafana is pre-configured with zero manual setup required:
- **Default Credentials**: `admin` / `stenovision_admin`
- **Datasource**: Pre-wired Prometheus (`http://prometheus:9090`)
- **Included Dashboard**: `StenoVision - Clinical AI & Infrastructure Overview`
  - *Panel 1*: Real-Time System Health & Uptime
  - *Panel 2*: Hardware Acceleration Mode (CUDA GPU vs CPU Fallback)
  - *Panel 3*: API Request Throughput (Req/Sec)
  - *Panel 4*: Deep Learning Inference Latency (P50, P95, P99)
  - *Panel 5*: Active Clinical Analyses Gauge
  - *Panel 6*: HTTP Error Rate & Exception Volume

---

## 4. HIPAA Safe Harbor Logging & Audit Trails

To comply with HIPAA Security and Privacy Rules (§ 164.312 and § 164.514), StenoVision implements structured JSON logging with real-time Protected Health Information (PHI) sanitization:

### Log Sanitization Features:
- **JSON Structure**: Emits machine-parsable logs with ISO-8601 timestamps, log level, logger name, and correlation IDs.
- **Request Tracing**: Injects a unique `X-Request-ID` into every HTTP transaction and response header for end-to-end tracing.
- **PHI Masking Engine**: Scans all log streams and automatically masks 18 HIPAA Safe Harbor identifiers:
  - Patient Names (`[REDACTED_NAME]`)
  - Medical Record Numbers (`[REDACTED_MRN]`)
  - Social Security Numbers (`[REDACTED_SSN]`)
  - Phone Numbers (`[REDACTED_PHONE]`)
  - Email Addresses (`[REDACTED_EMAIL]`)
- **Rotating Handlers**:
  - `backend/logs/stenovision.log`: All application and access events (10 MB max, 5 rotating backups).
  - `backend/logs/stenovision_error.log`: Error and critical severity events (10 MB max, 5 rotating backups).

### Sample Sanitized Log Record:
```json
{
  "timestamp": "2026-11-23T15:02:18.421Z",
  "level": "INFO",
  "logger": "stenovision.middleware",
  "request_id": "b18e7c90-951d-4074-9c8e-a2283cb9d0fe",
  "method": "POST",
  "path": "/api/v1/cases/analyze",
  "status_code": 200,
  "duration_ms": 712.4,
  "client_ip": "172.28.0.1",
  "message": "Completed case analysis for patient [REDACTED_NAME] MRN: [REDACTED_MRN]"
}
```

---

## 5. Verification & Healthchecks

Once deployed, verify all endpoints:

```bash
# 1. Unified Nginx Gateway Health
curl -I http://localhost/health

# 2. Detailed Backend & Model Diagnostics
curl http://localhost/health

# 3. Prometheus Metrics Endpoint
curl http://localhost/metrics | grep stenovision_

# 4. Master Automated Test Suite Execution
python tests/run_master_suite.py
```
Expected: All 8 test suites pass with 100% compliance score.
