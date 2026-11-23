import mimetypes
from pathlib import PureWindowsPath

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.case_deps import AccessibleCase, CaseWriter
from app.api.deps import DbSession
from app.core.config import settings
from app.crud import case_image as image_crud
from app.models.case import CaseStatus
from app.models.user import Role
from app.schemas.case_image import CaseImageRead
from app.services.storage import FileTooLargeError, UnsupportedFileTypeError, storage

router = APIRouter()


@router.post(
    "/{case_id}/images", response_model=CaseImageRead, status_code=status.HTTP_201_CREATED
)
def upload_image(case: AccessibleCase, user: CaseWriter, db: DbSession, file: UploadFile):
    if case.status in (CaseStatus.CLOSED, CaseStatus.ARCHIVED):
        raise HTTPException(status.HTTP_409_CONFLICT, "Images cannot be added to a closed case")

    try:
        stored = storage.save(file.file, file.filename or "", case.id)
    except UnsupportedFileTypeError:
        raise HTTPException(
            415, "Unsupported file type. Allowed: .png, .jpg, .jpeg, .dcm, .nii, .nii.gz"
        ) from None
    except FileTooLargeError:
        raise HTTPException(413, f"File is larger than {settings.MAX_UPLOAD_MB} MB") from None

    # Keep only the file name (no folders) and fit the column size.
    display_name = PureWindowsPath(file.filename or "").name[:255]
    try:
        return image_crud.create_image(
            db,
            case_id=case.id,
            uploaded_by_id=user.id,
            original_filename=display_name,
            stored=stored,
        )
    except Exception:
        storage.delete(stored.key)  # don't leave an orphan file if the DB write fails
        raise


@router.get("/{case_id}/images/{image_id}/file")
def download_image(case: AccessibleCase, image_id: int, db: DbSession):
    image = image_crud.get_image(db, case_id=case.id, image_id=image_id)
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    try:
        path = storage.resolve(image.file_key)
    except FileNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image file missing from storage") from None

    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=image.original_filename)


@router.delete("/{case_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(case: AccessibleCase, image_id: int, user: CaseWriter, db: DbSession) -> None:
    image = image_crud.get_image(db, case_id=case.id, image_id=image_id)
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    if user.role != Role.ADMIN and image.uploaded_by_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own uploads")

    key = image.file_key
    image_crud.delete_image(db, image)
    storage.delete(key)