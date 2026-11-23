from app.models.case import Case, CaseStatus
from app.models.user import Role, User

# Roles that may create/edit cases and upload images.
CASE_WRITER_ROLES = (
    Role.ADMINISTRATOR,
    Role.RADIOLOGIST_CLINICIAN,
    Role.DATA_SCIENTIST,
    Role.MEDICAL_RESEARCHER,
)


def can_view_case(user: User, case: Case) -> bool:
    if case.status == CaseStatus.ARCHIVED:
        return user.role == Role.ADMINISTRATOR
    return True
