# StenoVision — FastAPI Backend API Reference

Welcome to the backend microservice documentation for StenoVision.

## Overview
Our backend is built with **FastAPI** (Python 3.10+) and provides high-performance clinical endpoints for:
- User authentication and role-based access control (JWT bearer tokens).
- Patient and coronary angiogram case management.
- Deep learning inference pipeline (Attention U-Net, Faster R-CNN, ResNet-18, and Grad-CAM).
- Quantitative Coronary Angiography (QCA) caliper calculations (%DS, MLD, RVD).
- Automated ReportLab clinical PDF generation and CSV cohort streaming.
- Prometheus metrics exposition (`/metrics`) and health telemetry (`/health`).

---

## Interactive Documentation
When running the backend server on `http://127.0.0.1:8000`:
- **Swagger Interactive UI:** [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **ReDoc API Manual:** [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc)
- **Health Check & Telemetry:** [`http://127.0.0.1:8000/health`](http://127.0.0.1:8000/health)

---

## Key API Route Groups

| Route Prefix | Purpose | Required Role |
| :--- | :--- | :--- |
| `POST /api/v1/auth/login` | OAuth2 password flow; exchanges credentials for JWT token | Public |
| `GET /api/v1/cases` | Retrieves patient coronary angiogram cases with search & filtering | All Personas |
| `GET /api/v1/cases/{case_id}` | Detailed case inspection with multi-slice image references | All Personas |
| `POST /api/v1/cases/{case_id}/analysis` | Runs the full DL segmentation, QCA, and stenosis pipeline | Clinician, Researcher |
| `GET /api/v1/models` | Lists active neural network architectures and benchmark metrics | Data Scientist, Dev |
| `GET /api/v1/reports` | Directory of verified clinical diagnostic reports | All Personas |
| `POST /api/v1/reports/{id}/pdf` | Generates high-resolution ReportLab vector PDF document | Clinician, Admin |
| `GET /api/v1/users` | Platform identity and role-based access management | Administrator |
| `GET /metrics` | Prometheus metrics exposition for system telemetry | All Personas |

---

## How We Run the Backend

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database schema & sample clinical personnel
python -m backend.app.db.init_db

# 3. Start development server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
