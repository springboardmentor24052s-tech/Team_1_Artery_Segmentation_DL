import logging
from sqlalchemy import inspect, text
from app.core.config import settings
from app.core.security import get_password_hash
from app.crud import user as user_crud
from app.db.session import Base, SessionLocal, engine
from app.models.user import Role, User

logger = logging.getLogger("stenovision.init")

DEFAULT_PERSONNEL = [
    {
        "name": "Sathiya (Lead Dev)",
        "email": "sathiya@stenovision.ai",
        "role": Role.DEVELOPER,
        "department": "Lead AI & System Engineering",
        "password": "sathiyapassword123",
    },
    {
        "name": "Dr. Aris Thorne",
        "email": "a.thorne@stenovision.org",
        "role": Role.RADIOLOGIST_CLINICIAN,
        "department": "Clinical Diagnostics",
        "password": "thornepassword123",
    },
    {
        "name": "Prof. David Chen",
        "email": "d.chen@stenovision.org",
        "role": Role.MEDICAL_RESEARCHER,
        "department": "Cardiovascular Research",
        "password": "chenpassword123",
    },
    {
        "name": "Dr. Helena Rostova",
        "email": "h.rostova@stenovision.org",
        "role": Role.DATA_SCIENTIST,
        "department": "Data Science",
        "password": "rostovapassword123",
    },
    {
        "name": "Sophia Martinez",
        "email": "s.martinez@stenovision.org",
        "role": Role.ADMINISTRATOR,
        "department": "Administration",
        "password": "martinezpassword123",
    },
]


def _migrate_columns() -> None:
    """Safely apply schema additions for SQLite or local DB without dropping data."""
    with engine.connect() as conn:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if "users" in tables:
            user_cols = [c["name"] for c in inspector.get_columns("users")]
            if "department" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR(100) DEFAULT 'Cardiovascular Research'"))
            # Migrate legacy roles to the 4 official document roles
            conn.execute(text("UPDATE users SET role = 'RADIOLOGIST_CLINICIAN' WHERE role IN ('SENIOR_RADIOLOGIST', 'radiologist', 'senior_radiologist', 'Radiologist / Clinician')"))
            conn.execute(text("UPDATE users SET role = 'MEDICAL_RESEARCHER' WHERE role IN ('PRINCIPAL_INVESTIGATOR', 'principal_investigator', 'Medical Researcher')"))
            conn.execute(text("UPDATE users SET role = 'DATA_SCIENTIST' WHERE role IN ('AI_RESEARCH_FELLOW', 'LAB_TECHNICIAN', 'ai_research_fellow', 'lab_technician', 'Data Scientist')"))
            conn.execute(text("UPDATE users SET role = 'ADMINISTRATOR' WHERE role IN ('ADMIN', 'admin', 'Administrator')"))
            conn.execute(text("DELETE FROM users WHERE email = 'l.vance@stenovision.org' OR email = 'admin@stenovision.com'"))
            conn.commit()

        if "cases" in tables:
            case_cols = [c["name"] for c in inspector.get_columns("cases")]
            if "case_code" not in case_cols:
                conn.execute(text("ALTER TABLE cases ADD COLUMN case_code VARCHAR(50)"))
            if "patient_id_code" not in case_cols:
                conn.execute(text("ALTER TABLE cases ADD COLUMN patient_id_code VARCHAR(50)"))
            if "patient_name" not in case_cols:
                conn.execute(text("ALTER TABLE cases ADD COLUMN patient_name VARCHAR(120)"))
            if "age" not in case_cols:
                conn.execute(text("ALTER TABLE cases ADD COLUMN age INTEGER"))
            if "gender" not in case_cols:
                conn.execute(text("ALTER TABLE cases ADD COLUMN gender VARCHAR(20)"))
            conn.commit()

        if "case_images" in tables:
            img_cols = [c["name"] for c in inspector.get_columns("case_images")]
            if "storage_tier" not in img_cols:
                conn.execute(text("ALTER TABLE case_images ADD COLUMN storage_tier VARCHAR(50) DEFAULT 'raw'"))
            if "modality" not in img_cols:
                conn.execute(text("ALTER TABLE case_images ADD COLUMN modality VARCHAR(50) DEFAULT 'XCA'"))
            conn.commit()


def init_db() -> None:
    import app.models  # noqa: F401  (registers tables with Base)

    Base.metadata.create_all(bind=engine)
    _migrate_columns()

    with SessionLocal() as db:
        # Seed and synchronize default personnel accounts
        for p in DEFAULT_PERSONNEL:
            existing = user_crud.get_by_email(db, p["email"])
            if not existing:
                u = User(
                    email=p["email"],
                    full_name=p["name"],
                    hashed_password=get_password_hash(p["password"]),
                    role=p["role"],
                    department=p["department"],
                    is_active=True,
                )
                db.add(u)
            else:
                existing.role = p["role"]
                existing.full_name = p["name"]
        db.commit()
        logger.info("[DATABASE] Initialized schema and synchronized 5 platform personnel accounts.")
