# StenoVision Backend setup with secure logins, protected API endpoints, case management, image handling and complete database design

Backend and database module of **StenoVision**, a deep learning project for **artery segmentation and stenosis detection** from medical images. This service handles user accounts, role-based access, case management and image uploads, so the segmentation models and the frontend can connect to one secure API.

## Introduction

- **Project topic:** detecting and segmenting arteries in medical images and measuring stenosis (narrowing of a blood vessel).
- **What this module does:** lets users register and log in, controls what each role can do, and lets authorised staff create cases and attach medical images to them.
- **Where it fits:** the segmentation model and the web frontend will use this API to read cases and images and to store results.

## Topics Covered

- Authentication and authorisation (login, tokens, roles)
- Case management (create, view, update, archive)
- Medical image upload, validation and storage
- Relational database design (users, cases, case images)
- REST API design, validation and testing

## Tech Used

| Area | Technology |
|---|---|
| Language | Python 3.11+ |
| Web framework | FastAPI |
| Server | Uvicorn |
| Database | PostgreSQL |
| ORM and driver | SQLAlchemy 2.x, psycopg 3 |
| Validation and settings | Pydantic v2, pydantic-settings |
| Authentication | PyJWT (tokens), Passlib with bcrypt (password hashing) |
| File uploads | python-multipart, local disk storage |
| Code quality | Ruff |
| Version control | Git and GitHub (branch per team member) |
| API testing | Postman, Swagger UI |

| Swagger / OpenAPI | Auto-generated interactive API documentation at /docs |
| HTTP status codes | 200 OK, 201 Created, 401 Unauthorised, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Invalid input |


## Roles

`admin`, `radiologist`, `clinician`, `doctor`, `patient`, `data_scientist`. Public registration always creates a **patient**. Staff roles are assigned by an admin.

## Quick Start

```bash
git clone REPO_URL
cd StenoVisionBackend
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1      Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

1. Create a PostgreSQL database and user with `psql`.
2. Copy `.env.example` to `.env` and fill in `SECRET_KEY`, `DATABASE_URL`, `FIRST_ADMIN_EMAIL` and `FIRST_ADMIN_PASSWORD`.
3. Run the server from the project root:

```bash
uvicorn app.main:app --reload
```

## Useful Links

| What | URL |
|---|---|
| Swagger UI (try the API) | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |
| Health check | http://127.0.0.1:8000/health |

All API routes start with `/api/v1`.

## Project Structure

```
app/
├── main.py            # entry point, routers, /health
├── api/               # dependencies and routes (auth, users, cases, case_images)
├── core/              # config, security, permissions
├── crud/              # database queries
├── db/                # engine, session, first-admin setup
├── models/            # database tables
├── schemas/           # request and response shapes
└── services/          # file storage
```
