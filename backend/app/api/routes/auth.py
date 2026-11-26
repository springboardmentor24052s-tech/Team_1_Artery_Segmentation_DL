import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, DbSession
from app.core.metrics import AUTH_LOGINS_TOTAL
from app.core.middleware import extract_client_ip
from app.core.security import create_access_token, verify_password
from app.core.utils import utcnow
from app.crud import user as user_crud
from app.models.audit_log import LoginAuditLog
from app.models.user import Role
from app.schemas.user import Token, UserCreate, UserRead

router = APIRouter()
auth_logger = logging.getLogger("stenovision.auth")


def mask_email(email: str) -> str:
    """Partially masks an email address so logs never store plaintext PII."""
    clean = (email or "").strip().lower()
    if "@" not in clean:
        return "***"
    local, domain = clean.split("@", 1)
    prefix = local[:1] if local else "*"
    return f"{prefix}***@{domain}"


def _record_login_audit(
    db: DbSession,
    *,
    request: Request,
    email: str,
    user_id: int | None,
    user_role: str,
    outcome: str,
) -> None:
    """Persists login attempt to login_audit_logs and emits metric + structured log."""
    client_ip = extract_client_ip(request)
    user_agent = (request.headers.get("User-Agent") or "")[:255]
    request_id = getattr(request.state, "request_id", None)
    masked = mask_email(email)

    db.add(
        LoginAuditLog(
            user_id=user_id,
            user_role=user_role,
            attempted_email_masked=masked,
            outcome=outcome,
            client_ip=client_ip,
            user_agent=user_agent,
            request_id=request_id,
        )
    )
    db.commit()

    AUTH_LOGINS_TOTAL.labels(role=user_role, outcome=outcome).inc()
    log_level = logging.INFO if outcome == "success" else logging.WARNING
    auth_logger.log(
        log_level,
        f"Auth login {outcome} for user_id={user_id} role={user_role}",
        extra={
            "request_id": request_id,
            "client_ip": client_ip,
            "user_id": user_id,
            "user_role": user_role,
            "auth_outcome": outcome,
        },
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession):
    if user_crud.get_by_email(db, payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    # Public sign-up is ALWAYS a patient. Staff roles are assigned by an admin.
    return user_crud.create_user(
        db,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role=Role.PATIENT,
    )


@router.post("/login", response_model=Token)
def login(request: Request, form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    # OAuth2 form calls the field "username"; we use the email there.
    candidate = user_crud.get_by_email(db, form.username)
    if candidate is None or not verify_password(form.password, candidate.hashed_password):
        _record_login_audit(
            db,
            request=request,
            email=form.username,
            user_id=candidate.id if candidate else None,
            user_role=candidate.role if candidate else "unknown",
            outcome="invalid_credentials",
        )
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not candidate.is_active:
        _record_login_audit(
            db,
            request=request,
            email=form.username,
            user_id=candidate.id,
            user_role=candidate.role,
            outcome="inactive_account",
        )
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is deactivated")

    candidate.last_login_at = utcnow()
    _record_login_audit(
        db,
        request=request,
        email=form.username,
        user_id=candidate.id,
        user_role=candidate.role,
        outcome="success",
    )
    return Token(access_token=create_access_token(str(candidate.id)))


@router.get("/me", response_model=UserRead)
def read_me(current_user: CurrentUser):
    return current_user
