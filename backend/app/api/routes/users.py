from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select

from app.api.deps import DbSession, require_roles
from app.crud import user as user_crud
from app.models.audit_log import LoginAuditLog
from app.models.user import Role, User
from app.schemas.user import AdminUserCreate, LoginAuditEntry, RoleUpdate, UserAuditResponse, UserRead

router = APIRouter()


@router.get(
    "/",
    response_model=list[UserRead],
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def list_users(db: DbSession, skip: int = 0, limit: int = Query(50, le=100)):
    return user_crud.list_users(db, skip=skip, limit=limit)


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def create_user(payload: AdminUserCreate, db: DbSession):
    if user_crud.get_by_email(db, payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    return user_crud.create_user(
        db,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role=payload.role,
    )


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    dependencies=[Depends(require_roles(Role.ADMIN))],
)
def change_role(user_id: int, payload: RoleUpdate, db: DbSession):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user_crud.update_role(db, user, payload.role)


@router.get(
    "/audit",
    response_model=UserAuditResponse,
    dependencies=[Depends(require_roles(Role.ADMIN, Role.DEVELOPER))],
)
def get_login_audit(
    db: DbSession,
    limit: int = Query(50, ge=1, le=200),
):
    """Returns active user roster (with last_login_at) and recent login audit history."""
    total_events = db.scalar(select(func.count(LoginAuditLog.id))) or 0

    users = list(
        db.scalars(
            select(User).order_by(desc(User.last_login_at).nullslast(), User.id)
        )
    )

    rows = db.execute(
        select(LoginAuditLog, User.full_name)
        .outerjoin(User, LoginAuditLog.user_id == User.id)
        .order_by(desc(LoginAuditLog.created_at), desc(LoginAuditLog.id))
        .limit(limit)
    ).all()

    recent_logins = [
        LoginAuditEntry(
            id=audit.id,
            user_id=audit.user_id,
            full_name=full_name,
            user_role=audit.user_role,
            attempted_email_masked=audit.attempted_email_masked,
            outcome=audit.outcome,
            client_ip=audit.client_ip,
            user_agent=audit.user_agent,
            request_id=audit.request_id,
            created_at=audit.created_at,
        )
        for audit, full_name in rows
    ]

    return UserAuditResponse(
        total_events=total_events,
        active_users=users,
        recent_logins=recent_logins,
    )
