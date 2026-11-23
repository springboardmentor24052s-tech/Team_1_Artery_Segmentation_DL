"""JWT authentication, password hashing, RBAC and audit logging."""
from __future__ import annotations

import re
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import ACCESS_TOKEN_MINUTES, JWT_ALGORITHM, JWT_SECRET
from app.database import get_db
from app.models import AuditLog, User, UserSession

bearer = HTTPBearer(auto_error=False)

PASSWORD_RULE = "at least 8 characters with an uppercase letter, a lowercase letter, a digit and a symbol"


def validate_password(pw: str) -> None:
    if len(pw) < 8 or not re.search(r"[A-Z]", pw) or not re.search(r"[a-z]", pw) \
            or not re.search(r"\d", pw) or not re.search(r"[^A-Za-z0-9]", pw):
        raise HTTPException(400, f"Password must be {PASSWORD_RULE}.")


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except ValueError:
        return False


def create_session_token(db: Session, user: User, request: Request | None) -> str:
    jti = secrets.token_hex(16)
    exp = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    db.add(UserSession(id=jti, user_id=user.id, expires_at=exp,
                       user_agent=(request.headers.get("user-agent", "")[:300] if request else None),
                       ip=(request.client.host if request and request.client else None)))
    db.commit()
    return jwt.encode({"sub": str(user.id), "role": user.role, "jti": jti, "exp": exp}, JWT_SECRET, JWT_ALGORITHM)


def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired - please log in again.")
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication token.")


def get_current_user(request: Request, cred: HTTPAuthorizationCredentials | None = Depends(bearer),
                     db: Session = Depends(get_db)) -> User:
    token = cred.credentials if cred else request.query_params.get("token")  # token param for <img>/downloads
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated.")
    payload = _decode(token)
    sess = db.get(UserSession, payload.get("jti"))
    if sess is None or sess.revoked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session has been revoked.")
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account disabled.")
    request.state.jti = sess.id
    return user


def require_roles(*roles: str):
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role != "admin" and user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires role: {', '.join(roles) or 'admin'}.")
        return user
    return dep


# Permission groups
CLINICAL = ("radiologist",)
ANALYSTS = ("radiologist", "researcher")
ML_TEAM = ("data_scientist",)
ALL_ROLES = ("radiologist", "researcher", "data_scientist")


def audit(db: Session, user: User | None, action: str, entity: str | None = None, entity_id=None,
          detail: str | None = None, request: Request | None = None) -> None:
    db.add(AuditLog(user_id=user.id if user else None, user_email=user.email if user else None, action=action,
                    entity=entity, entity_id=str(entity_id) if entity_id is not None else None, detail=detail,
                    ip=request.client.host if request and request.client else None))
    db.commit()
