from fastapi import APIRouter, HTTPException, Query, status

from app.api.case_deps import AccessibleCase, AdminUser, CaseWriter
from app.api.deps import CurrentUser, DbSession
from app.crud import case as case_crud
from app.models.case import CaseStatus
from app.models.user import Role, User
from app.schemas.case import CaseCreate, CaseDetail, CaseList, CaseRead, CaseUpdate

router = APIRouter()


def _validate_patient(db: DbSession, patient_id: int | None) -> None:
    if patient_id is None:
        return
    patient = db.get(User, patient_id)
    if patient is None or patient.role != Role.PATIENT:
        raise HTTPException(422, "patient_id must belong to a user with the patient role")


@router.post("/", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreate, db: DbSession, user: CaseWriter):
    _validate_patient(db, payload.patient_id)
    return case_crud.create_case(db, data=payload, created_by=user)


@router.get("/", response_model=CaseList)
def list_cases(
    db: DbSession,
    user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: CaseStatus | None = Query(None, alias="status"),
):
    is_admin = user.role == Role.ADMIN
    if status_filter == CaseStatus.ARCHIVED and not is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins can list archived cases")

    items, total = case_crud.list_cases(
        db,
        patient_id=user.id if user.role == Role.PATIENT else None,
        status=status_filter,
        include_archived=is_admin,
        skip=skip,
        limit=limit,
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/{case_id}", response_model=CaseDetail)
def read_case(case: AccessibleCase):
    return case


@router.patch("/{case_id}", response_model=CaseRead)
def update_case(payload: CaseUpdate, case: AccessibleCase, db: DbSession, _user: CaseWriter):
    if payload.status == CaseStatus.ARCHIVED:
        raise HTTPException(422, "Use DELETE to archive a case")
    if "patient_id" in payload.model_fields_set:
        _validate_patient(db, payload.patient_id)
    return case_crud.update_case(db, case, payload)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_case(case: AccessibleCase, db: DbSession, _admin: AdminUser) -> None:
    case_crud.archive_case(db, case)