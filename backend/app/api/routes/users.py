from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DbSession, require_roles
from app.crud import user as user_crud
from app.models.user import Role, User
from app.schemas.user import AdminUserCreate, RoleUpdate, UserRead

# Every route in this router requires the ADMIN role.
router = APIRouter(dependencies=[Depends(require_roles(Role.ADMIN))])


@router.get("/", response_model=list[UserRead])
def list_users(db: DbSession, skip: int = 0, limit: int = Query(50, le=100)):
    return user_crud.list_users(db, skip=skip, limit=limit)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
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


@router.patch("/{user_id}/role", response_model=UserRead)
def change_role(user_id: int, payload: RoleUpdate, db: DbSession):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user_crud.update_role(db, user, payload.role)