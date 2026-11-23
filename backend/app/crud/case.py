from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.case import Case, CaseStatus
from app.models.user import User
from app.schemas.case import CaseCreate, CaseUpdate


def create_case(db: Session, *, data: CaseCreate, created_by: User) -> Case:
    case = Case(**data.model_dump(), created_by_id=created_by.id)
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_case(db: Session, case_id: int) -> Case | None:
    stmt = select(Case).where(Case.id == case_id).options(selectinload(Case.images))
    return db.scalar(stmt)


def list_cases(
    db: Session,
    *,
    patient_id: int | None = None,
    status: CaseStatus | None = None,
    include_archived: bool = False,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Case], int]:
    stmt = select(Case)
    if patient_id is not None:
        stmt = stmt.where(Case.patient_id == patient_id)
    if status is not None:
        stmt = stmt.where(Case.status == status)
    elif not include_archived:
        stmt = stmt.where(Case.status != CaseStatus.ARCHIVED)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Case.created_at.desc()).offset(skip).limit(limit))
    return list(rows), total


def update_case(db: Session, case: Case, data: CaseUpdate) -> Case:
    # exclude_unset=True -> only fields the client actually sent
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(case, field, value)
    db.commit()
    db.refresh(case)
    return case


def archive_case(db: Session, case: Case) -> Case:
    case.status = CaseStatus.ARCHIVED
    db.commit()
    db.refresh(case)
    return case