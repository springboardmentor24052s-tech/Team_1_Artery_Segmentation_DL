# StenoVision Modular Clinical Quality Assurance & Verification Suite

Comprehensive, enterprise-grade automated testing suite for **StenoVision**—an AI-assisted coronary angiography stenosis detection and Quantitative Coronary Arteriography (QCA) clinical decision support platform.

This dedicated testing module provides isolated, production-grade verification across four critical testing disciplines:
1. **End-to-End (E2E) Testing**: Real browser UI interaction across all 5 clinical user roles and 6-stage deep learning diagnostic pipeline validation.
2. **REST API Microservices Testing**: Route contracts, query parametrization, schema verification, and programmatic RBAC matrix enforcement.
3. **Enterprise Security & Regulatory Compliance Testing**: Cryptographic JWT validation, HIPAA Safe Harbor Method de-identification audit, 5-role clinical authority boundaries, SQL injection (SQLi) immunity, Cross-Site Scripting (XSS) sanitization, and path traversal rejection.
4. **Performance & Stress Benchmarking**: Sub-35ms inference latency, real-time medical cine-fluoroscopy frame rate ($\ge 25.0 \text{ FPS}$), sub-second clinical PDF compilation SLA ($< 500 \text{ ms}$), high-volume burst throughput stress (350+ RPS), and dynamic heap memory leak profiling (`tracemalloc`).

---

## 1. Directory Architecture

All tests, runners, visual evidence screenshots, execution logs, and structured machine-readable result files are isolated inside this directory:

```
StenoVision/test_suite/
├── README.md                          # Comprehensive technical manual & execution guide (this file)
├── __init__.py
├── run_master_suite.py                # Central CLI orchestrator and aggregator
│
├── e2e/                               # 1. End-to-End Testing Discipline
│   ├── __init__.py
│   ├── test_e2e_pipeline.py           # 6-stage headless DL pipeline (Ingest -> U-Net -> Calipers -> ResNet-18 -> XAI -> Reports)
│   └── test_e2e_browser_operations.py # 12-phase live Playwright browser automation against http://localhost:3000
│
├── api/                               # 2. REST API Microservices Testing Discipline
│   ├── __init__.py
│   ├── test_api_endpoints.py          # 7 FastAPI REST endpoint groups (Health, Auth, Cases, Models, Reports)
│   └── test_api_rbac_matrix.py        # Programmatic suitability matrix and permissions verification
│
├── security/                          # 3. Enterprise Security & HIPAA Audit Discipline
│   ├── __init__.py
│   ├── test_security_audit.py         # 7-vector security suite (JWT tamper, 5-role 403s, SQLi, XSS, traversal, CORS)
│   └── test_hipaa_compliance.py       # HIPAA Safe Harbor audit (18 direct identifiers & ANON-xxxx de-ID)
│
├── performance/                       # 4. Performance, Latency & Stress Discipline
│   ├── __init__.py
│   ├── test_performance_benchmarks.py # DL latency (<35ms), cine-fluoroscopy (>=25 FPS), PDF compilation SLA (<500ms)
│   └── test_burst_stress_and_memory.py# Burst RPS stress testing & tracemalloc heap memory leak profiling
│
├── results/                           # Persistent Machine-Readable Test Summaries
│   ├── e2e_results.json               # E2E pipeline & phase execution metrics
│   ├── api_results.json               # API endpoint status codes & latencies
│   ├── security_results.json          # Security vector audit findings & 403 boundaries
│   ├── performance_results.json       # Latency distributions, FPS throughput, RPS, heap deltas
│   ├── master_scorecard.json          # Unified machine-readable JSON scorecard
│   └── master_scorecard.md            # Human-readable clinical QA markdown scorecard
│
├── evidence/                          # Visual Proof Screenshots Captured during E2E Operations
│   ├── rbac_01_researcher_deidentified_cases.png
│   ├── rbac_02_researcher_upload_deid.png
│   ├── rbac_03_developer_signoff_restricted.png
│   ├── rbac_04_clinician_signoff_authorized.png
│   ├── rbac_05_researcher_readonly_directory.png
│   ├── e2e_generate_report_modal_solid.png
│   └── e2e_report_detail_modal_solid.png
│
└── logs/                              # Execution Logs & Transcripts
    ├── e2e.log
    ├── api.log
    ├── security.log
    ├── performance.log
    └── master_run.log
```

---

## 2. Regulatory Baselines & Clinical Standards

StenoVision is designed for deployment in hospital cath-labs and cardiology imaging suites. The test suite enforces rigorous regulatory and clinical thresholds:

| Metric / Standard | Regulatory Baseline | Verification Module | Target Threshold |
| :--- | :--- | :--- | :---: |
| **Cine-Fluoroscopy Frame Rate** | DICOM Medical Imaging Standard (ISO/IEEE) | `performance/test_performance_benchmarks.py` | $\mathbf{\ge 25.0 \text{ FPS}}$ ($< 40 \text{ ms}$ latency) |
| **Model Inference Latency** | Real-Time Clinical Decision Support SLA | `performance/test_performance_benchmarks.py` | $\mathbf{< 35.0 \text{ ms}}$ mean latency |
| **Document Compilation SLA** | Automated EHR Clinical Report Generation | `performance/test_performance_benchmarks.py` | $\mathbf{< 500.0 \text{ ms}}$ Sub-Second SLA |
| **High-Volume Burst Throughput** | Multi-User Hospital Concurrent Querying | `performance/test_burst_stress_and_memory.py` | $\mathbf{> 200 \text{ RPS}}$, $\mathbf{0.0\%}$ error rate |
| **Heap Memory Leak Stability** | 24/7 Hospital Server Continuous Deployment | `performance/test_burst_stress_and_memory.py` | $\mathbf{< 1.000 \text{ MB}}$ delta over heavy cycles |
| **HIPAA Safe Harbor Privacy** | 45 CFR § 164.514(b)(2) (Safe Harbor Method) | `security/test_hipaa_compliance.py` | $\mathbf{0}$ of 18 direct identifiers present |
| **Physician Sign-Off Separation** | Medical Legal Authority Separation | `security/test_security_audit.py` | Strict $\mathbf{\text{HTTP } 403}$ for non-clinicians |
| **Model Deployment Boundary** | Clinical Governance & Neural Safety | `security/test_security_audit.py` | Strict $\mathbf{\text{HTTP } 403}$ for non-engineers |
| **SQL Injection (SQLi) Shield** | OWASP Top 10 A03:2021-Injection | `security/test_security_audit.py` | $\mathbf{100\%}$ Parameterized ORM Defusal |
| **Arbitrary Traversal / Upload** | OWASP Top 10 A01:2021-Broken Access | `security/test_security_audit.py` | $\mathbf{100\%}$ Blocked (`HTTP 404/403`) |

---

## 3. Prerequisites & Environment Setup

### 1. Python Environment & Dependencies
Ensure Python 3.10+ is active. Required packages:
```bash
pip install fastapi uvicorn pydantic sqlalchemy httpx reportlab pillow plotly playwright
```

### 2. Playwright Chromium Driver (for E2E Browser Testing)
Ensure Playwright browser binaries are installed:
```bash
playwright install chromium
```

### 3. Server Daemons (Required for E2E Browser Testing)
For live browser automation, launch the backend and frontend dev servers:
```bash
# Terminal 1: FastAPI Backend
cd StenoVision/backend
python -m uvicorn app.main:app --port 8000 --host 127.0.0.1

# Terminal 2: Next.js Frontend
cd StenoVision/frontend
npm run dev
```

---

## 4. Execution Commands

### Run Everything via the Master Orchestrator
To execute all test suites sequentially, compile the unified clinical quality scorecard, and save all outputs:
```bash
python StenoVision/test_suite/run_master_suite.py
```

### Run Individual Test Disciplines

#### 1. End-to-End (E2E) Testing
- **Headless Deep Learning Pipeline**:
  ```bash
  python StenoVision/test_suite/e2e/test_e2e_pipeline.py
  ```
- **Live Playwright Browser Operations & Visual Capture**:
  ```bash
  python StenoVision/test_suite/e2e/test_e2e_browser_operations.py
  ```

#### 2. REST API Microservices Testing
- **Endpoints & Schemas**:
  ```bash
  python StenoVision/test_suite/api/test_api_endpoints.py
  ```
- **RBAC Matrix Programmatic Assertions**:
  ```bash
  python StenoVision/test_suite/api/test_api_rbac_matrix.py
  ```

#### 3. Security & Regulatory Compliance Testing
- **Enterprise Security Audit (7 Vectors)**:
  ```bash
  python StenoVision/test_suite/security/test_security_audit.py
  ```
- **HIPAA Safe Harbor Compliance**:
  ```bash
  python StenoVision/test_suite/security/test_hipaa_compliance.py
  ```

#### 4. Performance & Stress Benchmarking
- **DL Latency, Cine-Fluoroscopy FPS & PDF SLA**:
  ```bash
  python StenoVision/test_suite/performance/test_performance_benchmarks.py
  ```
- **Burst Concurrency RPS & Memory Leak Profiling**:
  ```bash
  python StenoVision/test_suite/performance/test_burst_stress_and_memory.py
  ```

---

## 5. Result Interpretation & Persistent Artifacts

### 1. Machine-Readable Results (`test_suite/results/`)
- `master_scorecard.json`: Contains high-level metadata (timestamp, total suites, pass count, total execution time) and nested granular metrics per suite.
- `master_scorecard.md`: Formatted markdown clinical scorecard suitable for export into regulatory submissions and project documentation.
- Individual JSON reports:
  - `e2e_results.json`: Status of all 6 pipeline stages and 12 browser interaction phases.
  - `api_results.json`: Status codes, response times, and payload schemas for all 7 REST endpoint groups.
  - `security_results.json`: Vulnerability test findings, 403 boundary verifications, and HIPAA compliance confirmations.
  - `performance_results.json`: Latency percentiles ($p_{50}, p_{90}, p_{95}, p_{99}$), FPS throughput, RPS burst metrics, and net heap memory delta in MB.

### 2. Visual Proof Screenshots (`test_suite/evidence/`)
High-resolution `.png` screenshots automatically captured during browser E2E operations:
- `rbac_01_researcher_deidentified_cases.png`: Validates HIPAA Safe Harbor `ANON-xxxx [De-Identified]` masking in cohort case listings.
- `rbac_02_researcher_upload_deid.png`: Validates cohort scan ingestion and consensus-locked production best-model (`Cascade v2.1`) execution.
- `rbac_03_developer_signoff_restricted.png`: Validates that non-clinicians see the electronic sign-off button disabled with the explanatory clinical notice.
- `rbac_04_clinician_signoff_authorized.png`: Validates that licensed attending clinicians can countersign diagnostic reports.
- `rbac_05_researcher_readonly_directory.png`: Validates that Medical Researchers see a read-only personnel directory without user provisioning buttons.
- `e2e_generate_report_modal_solid.png`: Validates pure solid white background (`rgb(255, 255, 255)`) and 100% opacity on the diagnostic report modal.

### 3. Execution Logs (`test_suite/logs/`)
Full stdout/stderr traces for every test suite execution, timestamped and preserved for auditing.

---

## 6. Troubleshooting & FAQ

- **Database Connection Warning**:
  - `[DATABASE] Primary PostgreSQL ... is not reachable ... Activating persistent local fallback (sqlite:///./stenovision.db)`:
  - This is expected behavior during local offline testing. The system automatically switches to SQLite fallback to maintain uninterrupted testing.
- **Port 8000 / 3000 In Use**:
  - If backend or frontend fail to bind, check existing processes using PowerShell:
    ```powershell
    Get-NetTCPConnection -LocalPort 8000, 3000 -ErrorAction SilentlyContinue
    ```
- **Playwright Timeout**:
  - Ensure the Next.js frontend is actively serving on `http://localhost:3000` before running `test_e2e_browser_operations.py`.
