from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case_image import CaseImage
from app.services.storage import StoredFile


def create_image(
    db: Session,
    *,
    case_id: int,
    uploaded_by_id: int,
    original_filename: str,
    stored: StoredFile,
) -> CaseImage:
    image = CaseImage(
        case_id=case_id,
        uploaded_by_id=uploaded_by_id,
        original_filename=original_filename,
        file_key=stored.key,
        file_size=stored.size_bytes,
        sha256=stored.sha256,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def get_image(db: Session, *, case_id: int, image_id: int) -> CaseImage | None:
    # Filtering by BOTH ids stops someone fetching image 5 through case 9
    # when image 5 belongs to a different case.
    stmt = select(CaseImage).where(CaseImage.id == image_id, CaseImage.case_id == case_id)
    return db.scalar(stmt)


def delete_image(db: Session, image: CaseImage) -> None:
    db.delete(image)
    db.commit()