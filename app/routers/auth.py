import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import LOGIN_RATE_LIMIT_PER_MIN
from app.database import get_db
from app.ratelimit import RateLimiter
from app.models import AuditLog, User, UserSession
from app.schemas import AdminUserUpdate, LoginIn, PasswordChange, ProfileUpdate, RegisterIn, TokenOut, UserOut
from app.security import (audit, create_session_token, get_current_user, hash_password, require_roles,
                          validate_password, verify_password)

router = APIRouter(prefix="/api/auth", tags=["auth"])
users_router = APIRouter(prefix="/api/users", tags=["users"])

MAX_FAILED = 5
login_limiter = RateLimiter(LOGIN_RATE_LIMIT_PER_MIN, 60)


def _check_login_rate(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    allowed, retry = login_limiter.check(ip)
    if not allowed:
        raise HTTPException(429, "Too many attempts from this address. Please wait and try again.",
                            headers={"Retry-After": str(int(retry) + 1)})


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, request: Request, db: Session = Depends(get_db)):
    _check_login_rate(request)
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(409, "An account with this email already exists.")
    validate_password(body.password)
    user = User(email=body.email, full_name=body.full_name.strip(), password_hash=hash_password(body.password),
                role=body.role, organization=body.organization)
    db.add(user)
    db.commit()
    audit(db, user, "register", "user", user.id, f"role={user.role}", request)
    token = create_session_token(db, user, request)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    _check_login_rate(request)
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if user and user.failed_logins >= MAX_FAILED:
        audit(db, user, "login_locked", "user", user.id, None, request)
        raise HTTPException(423, "Account locked after repeated failed logins. Contact an administrator.")
    if not user or not verify_password(body.password, user.password_hash):
        if user:
            user.failed_logins += 1
            db.commit()
        audit(db, user, "login_failed", "user", user.id if user else None, body.email, request)
        raise HTTPException(401, "Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(403, "Account is disabled.")
    user.failed_logins = 0
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    token = create_session_token(db, user, request)
    audit(db, user, "login", "user", user.id, None, request)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/token", response_model=TokenOut, include_in_schema=True)
def token(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password grant (form fields `username` and `password`), for standard OAuth2 clients and the
    Swagger 'Authorize' button. `username` is the account e-mail. Same checks as /login."""
    return login(LoginIn(email=form.username, password=form.password), request, db)


@router.post("/logout")
def logout(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sess = db.get(UserSession, request.state.jti)
    if sess:
        sess.revoked = True
        db.commit()
    audit(db, user, "logout", "user", user.id, None, request)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserOut)
def update_me(body: ProfileUpdate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.full_name:
        user.full_name = body.full_name.strip()
    if body.organization is not None:
        user.organization = body.organization
    db.commit()
    audit(db, user, "profile_update", "user", user.id, None, request)
    return user


@router.post("/change-password")
def change_password(body: PasswordChange, request: Request, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect.")
    validate_password(body.new_password)
    user.password_hash = hash_password(body.new_password)
    # revoke all other sessions
    for s in db.scalars(select(UserSession).where(UserSession.user_id == user.id, UserSession.id != request.state.jti)):
        s.revoked = True
    db.commit()
    audit(db, user, "password_change", "user", user.id, None, request)
    return {"ok": True}


@router.get("/sessions")
def my_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(UserSession).where(UserSession.user_id == user.id).order_by(UserSession.created_at.desc()).limit(20))
    return [{"id": s.id[:8], "created_at": s.created_at, "expires_at": s.expires_at, "revoked": s.revoked,
             "user_agent": s.user_agent, "ip": s.ip} for s in rows]


# ---------------------------------------------------------------- admin
@users_router.get("", response_model=list[UserOut])
def list_users(_: User = Depends(require_roles()), db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.id)).all()


@users_router.patch("/{user_id}", response_model=UserOut)
def admin_update(user_id: int, body: AdminUserUpdate, request: Request, admin: User = Depends(require_roles()),
                 db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    if u.id == admin.id and (body.role not in (None, "admin") or body.is_active is False):
        raise HTTPException(400, "You cannot demote or disable your own account.")
    if body.role:
        u.role = body.role
    if body.is_active is not None:
        u.is_active = body.is_active
        if body.is_active:
            u.failed_logins = 0
    db.commit()
    audit(db, admin, "user_update", "user", u.id, body.model_dump_json(exclude_none=True), request)
    return u


@users_router.post("/{user_id}/reset-password")
def admin_reset_password(user_id: int, request: Request, admin: User = Depends(require_roles()),
                         db: Session = Depends(get_db)):
    """Administrator password reset. Generates a temporary password that is shown to the administrator once;
    it is never written to the logs. All of the user's sessions are revoked and the lockout counter is cleared.
    The user should change it under Profile after signing in (this is guidance; it is not enforced)."""
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    if u.id == admin.id:
        raise HTTPException(400, "Use 'Change password' on your own profile.")
    temp = secrets.token_urlsafe(12) + "Aa1!"  # always meets the password policy
    u.password_hash = hash_password(temp)
    u.failed_logins = 0
    for s_ in db.scalars(select(UserSession).where(UserSession.user_id == u.id)):
        s_.revoked = True
    db.commit()
    audit(db, admin, "password_reset", "user", u.id, f"temporary password issued for {u.email}", request)
    return {"email": u.email, "temporary_password": temp}


@users_router.get("/audit-logs")
def audit_logs(limit: int = 200, _: User = Depends(require_roles()), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(min(limit, 1000)))
    return [{"id": r.id, "user": r.user_email, "action": r.action, "entity": r.entity, "entity_id": r.entity_id,
             "detail": r.detail, "ip": r.ip, "created_at": r.created_at} for r in rows]
