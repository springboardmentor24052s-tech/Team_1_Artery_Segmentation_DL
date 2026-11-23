"""ARTERIX - Milestone 1 backend (weeks 1-2).

Authentication with roles, patient and case management, medical image upload with validation, and the
preprocessing pipeline. Run:  uvicorn app.main:app --reload   then open http://localhost:8000/docs
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.config import ADMIN_EMAIL, ADMIN_PASSWORD, API_RATE_LIMIT_PER_MIN
from app.database import Base, SessionLocal, engine
from app.models import User
from app.ratelimit import RateLimiter
from app.routers import auth, cases
from app.security import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("arterix")
api_limiter = RateLimiter(API_RATE_LIMIT_PER_MIN, 60)


def startup():
    """Create the database tables and a first administrator account."""
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.scalar(select(User).where(User.role == "admin")):
            db.add(User(email=ADMIN_EMAIL, full_name="System Administrator", role="admin",
                        password_hash=hash_password(ADMIN_PASSWORD)))
            db.commit()
            log.info("Created default admin %s - change its password after the first login", ADMIN_EMAIL)


@asynccontextmanager
async def lifespan(_app):
    startup()
    yield


app = FastAPI(lifespan=lifespan, title="ARTERIX - Milestone 1 API", version="1.0.0",
              description="Authentication, patient and case management, image upload and preprocessing.")
app.add_middleware(CORSMiddleware,
                   allow_origins=["http://localhost:5173", "http://localhost:8000"],
                   allow_methods=["*"], allow_headers=["Authorization", "Content-Type"])


@app.middleware("http")
async def gateway(request: Request, call_next):
    """Rate limiting, response timing and security headers."""
    t0 = time.perf_counter()
    if request.url.path.startswith("/api/") and request.url.path != "/api/health":
        allowed, retry = api_limiter.check(request.client.host if request.client else "unknown")
        if not allowed:
            return JSONResponse(status_code=429, content={"detail": "Too many requests. Please slow down."},
                                headers={"Retry-After": str(int(retry) + 1)})
    resp = await call_next(request)
    resp.headers["X-Response-Time-ms"] = f"{(time.perf_counter() - t0) * 1000:.1f}"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    return resp


for r in (auth.router, auth.users_router, cases.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"status": "ok", "milestone": 1}
