from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.core.permissions import CASE_WRITER_ROLES, can_view_case
from app.crud import case as case_crud
from app.models.case import Case
from app.models.user import Role, User

CaseWriter = Annotated[User, Depends(require_roles(*CASE_WRITER_ROLES))]
AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]


def get_accessible_case(case_id: int, db: DbSession, current_user: CurrentUser) -> Case:
    """Load the case from the URL and make sure this user may see it."""
    case = case_crud.get_case(db, case_id)
    if case is None or not can_view_case(current_user, case):
        # 404 for both: we don't reveal that a hidden case exists.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    return case


AccessibleCase = Annotated[Case, Depends(get_accessible_case)]