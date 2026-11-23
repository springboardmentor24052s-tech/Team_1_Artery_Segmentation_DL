"""Patient & case management + medical image upload."""
import uuid

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import MAX_UPLOAD_MB, UPLOAD_DIR
from app.database import get_db
from app.ml.preprocessing import ImageValidationError, load_image
from app.models import Analysis, Case, ImageStudy, Patient, User
from app.schemas import AnalysisOut, CaseIn, CaseOut, ImageOut, PatientIn, PatientOut
from app.security import ALL_ROLES, ANALYSTS, CLINICAL, audit, require_roles
from app.storage import read_protected, remove_stored_files, write_protected

router = APIRouter(prefix="/api", tags=["patients & cases"])


def _case_files(cases) -> tuple[list[Path], list[Path]]:
    """Stored image files and analysis result folders belonging to the given cases."""
    files, folders = [], []
    for c in cases:
        files.extend(Path(img.stored_path) for img in c.images)
        folders.extend(Path(a.result_dir) for a in c.analyses if a.result_dir)
    return files, folders


# ------------------------------------------------------------------ patients
@router.get("/patients")
def list_patients(q: str | None = None, _: User = Depends(require_roles(*ALL_ROLES)), db: Session = Depends(get_db)):
    stmt = select(Patient).order_by(Patient.id.desc())
    if q:
        stmt = stmt.where(Patient.patient_code.ilike(f"%{q}%"))
    out = []
    for p in db.scalars(stmt):
        d = PatientOut.model_validate(p).model_dump()
        d["n_cases"] = len(p.cases)
        out.append(d)
    return out


@router.post("/patients", response_model=PatientOut, status_code=201)
def create_patient(body: PatientIn, request: Request, user: User = Depends(require_roles(*ANALYSTS)),
                   db: Session = Depends(get_db)):
    if db.scalar(select(Patient).where(Patient.patient_code == body.patient_code)):
        raise HTTPException(409, "Patient ID already exists.")
    p = Patient(**body.model_dump(), created_by=user.id)
    db.add(p)
    db.commit()
    audit(db, user, "patient_create", "patient", p.id, p.patient_code, request)
    return p


@router.get("/patients/{pid}", response_model=PatientOut)
def get_patient(pid: int, _: User = Depends(require_roles(*ALL_ROLES)), db: Session = Depends(get_db)):
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    return p


@router.put("/patients/{pid}", response_model=PatientOut)
def update_patient(pid: int, body: PatientIn, request: Request, user: User = Depends(require_roles(*ANALYSTS)),
                   db: Session = Depends(get_db)):
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.commit()
    audit(db, user, "patient_update", "patient", p.id, None, request)
    return p


@router.delete("/patients/{pid}")
def delete_patient(pid: int, request: Request, user: User = Depends(require_roles(*CLINICAL)), db: Session = Depends(get_db)):
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    files, folders = _case_files(p.cases)  # read the paths before the rows are gone
    db.delete(p)
    db.commit()
    removed, failed = remove_stored_files(files, folders)  # files go only after the database commit
    audit(db, user, "patient_delete", "patient", pid, f"files removed={removed} failed={failed}", request)
    return {"ok": True, "files_removed": removed, "files_failed": failed}


# --------------------------------------------------------------------- cases
def _case_dict(db: Session, c: Case) -> dict:
    d = CaseOut.model_validate(c).model_dump()
    d["patient_code"] = c.patient.patient_code
    last = db.scalar(select(Analysis).where(Analysis.case_id == c.id).order_by(Analysis.id.desc()))
    d["n_images"] = len(c.images)
    d["n_analyses"] = len(c.analyses)
    d["last_severity"] = last.overall_severity if last else None
    d["last_analysis_id"] = last.id if last else None
    d["model_version"] = (last.model_versions or {}).get("vessel_segmentation") if last else None
    return d


@router.get("/cases")
def list_cases(status: str | None = None, patient_id: int | None = None, q: str | None = None,
               _: User = Depends(require_roles(*ALL_ROLES)), db: Session = Depends(get_db)):
    stmt = select(Case).order_by(Case.id.desc())
    if status:
        stmt = stmt.where(Case.status == status)
    if patient_id:
        stmt = stmt.where(Case.patient_id == patient_id)
    if q:
        stmt = stmt.join(Patient).where(Case.case_code.ilike(f"%{q}%") | Patient.patient_code.ilike(f"%{q}%"))
    return [_case_dict(db, c) for c in db.scalars(stmt)]


@router.post("/cases", status_code=201)
def create_case(body: CaseIn, request: Request, user: User = Depends(require_roles(*ANALYSTS)), db: Session = Depends(get_db)):
    if not db.get(Patient, body.patient_id):
        raise HTTPException(404, "Patient not found")
    n = (db.scalar(select(func.max(Case.id))) or 0) + 1
    c = Case(case_code=f"CASE-{n:05d}", created_by=user.id, **body.model_dump())
    db.add(c)
    db.commit()
    audit(db, user, "case_create", "case", c.id, c.case_code, request)
    return _case_dict(db, c)


@router.get("/cases/{cid}")
def get_case(cid: int, _: User = Depends(require_roles(*ALL_ROLES)), db: Session = Depends(get_db)):
    c = db.get(Case, cid)
    if not c:
        raise HTTPException(404, "Case not found")
    d = _case_dict(db, c)
    d["patient"] = PatientOut.model_validate(c.patient).model_dump()
    d["images"] = [ImageOut.model_validate(i).model_dump() for i in c.images]
    d["analyses"] = [AnalysisOut.model_validate(a).model_dump() for a in sorted(c.analyses, key=lambda a: -a.id)]
    return d


@router.delete("/cases/{cid}")
def delete_case(cid: int, request: Request, user: User = Depends(require_roles(*CLINICAL)), db: Session = Depends(get_db)):
    c = db.get(Case, cid)
    if not c:
        raise HTTPException(404, "Case not found")
    files, folders = _case_files([c])  # read the paths before the rows are gone
    db.delete(c)
    db.commit()
    removed, failed = remove_stored_files(files, folders)  # files go only after the database commit
    audit(db, user, "case_delete", "case", cid, f"files removed={removed} failed={failed}", request)
    return {"ok": True, "files_removed": removed, "files_failed": failed}


@router.post("/cases/{cid}/images", response_model=ImageOut, status_code=201)
async def upload_image(cid: int, request: Request, file: UploadFile = File(...),
                       user: User = Depends(require_roles(*ANALYSTS)), db: Session = Depends(get_db)):
    c = db.get(Case, cid)
    if not c:
        raise HTTPException(404, "Case not found")
    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_UPLOAD_MB} MB.")
    try:
        loaded = load_image(data, file.filename or "upload.png")
    except ImageValidationError as e:
        raise HTTPException(422, str(e))
    ext = (file.filename or "x.png").rsplit(".", 1)[-1].lower()
    dest = UPLOAD_DIR / f"case{cid}_{uuid.uuid4().hex[:10]}.{ext}"
    stored = write_protected(dest, data)  # encrypted at rest; the plain file is never written
    img = ImageStudy(case_id=cid, filename=file.filename or dest.name, stored_path=str(stored), file_format=loaded.source_format,
                     width=loaded.original_shape[1], height=loaded.original_shape[0],
                     pixel_spacing_mm=loaded.pixel_spacing_mm)
    db.add(img)
    if c.status == "created":
        c.status = "uploaded"
    db.commit()
    audit(db, user, "image_upload", "image", img.id, f"case={c.case_code} file={img.filename}", request)
    return img


@router.get("/images/{iid}/file")
def image_file(iid: int, _: User = Depends(require_roles(*ALL_ROLES)), db: Session = Depends(get_db)):
    img = db.get(ImageStudy, iid)
    if not img:
        raise HTTPException(404, "Image not found")
    media = {"PNG": "image/png", "JPG": "image/jpeg", "JPEG": "image/jpeg", "BMP": "image/bmp",
             "TIF": "image/tiff", "TIFF": "image/tiff"}.get(img.file_format.upper(), "application/octet-stream")
    return Response(read_protected(Path(img.stored_path)), media_type=media,
                    headers={"Content-Disposition": f'inline; filename="{Path(img.filename).name}"',
                             "Cache-Control": "private, no-store"})
