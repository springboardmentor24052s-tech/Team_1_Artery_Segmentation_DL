from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.utils import utcnow
from app.db.session import Base


class LoginAuditLog(Base):
    """Stores per-attempt authentication audit records without exposing plaintext PHI/passwords."""

    __tablename__ = "login_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), index=True, default=None)
    user_role: Mapped[str] = mapped_column(String(60), default="unknown")
    attempted_email_masked: Mapped[str] = mapped_column(String(120), default="")
    outcome: Mapped[str] = mapped_column(String(32), index=True)
    client_ip: Mapped[str] = mapped_column(String(64), default="unknown")
    user_agent: Mapped[str] = mapped_column(String(255), default="")
    request_id: Mapped[Optional[str]] = mapped_column(String(64), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
