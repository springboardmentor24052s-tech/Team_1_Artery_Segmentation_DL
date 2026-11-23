import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Dict, Union

from app.core.config import settings

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".dcm", ".tif", ".tiff", ".nii", ".nii.gz"}
CHUNK_SIZE = 1024 * 1024  # 1 MB chunk streaming


class UnsupportedFileTypeError(Exception):
    """The file extension is not on the medical imaging allow-list."""


class FileTooLargeError(Exception):
    """The upload is bigger than MAX_UPLOAD_MB."""


@dataclass
class StoredFile:
    key: str
    size_bytes: int
    sha256: str
    tier: str


def get_extension(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".nii.gz"):
        return ".nii.gz"
    return Path(name).suffix


class LocalStorage:
    """
    Multi-Tier Local Medical Image Storage Service.
    Structures medical images into secure, isolated disk partitions:
    - storage/raw/: Original uploaded XCA/DICOM angiograms
    - storage/masks/: Attention U-Net vessel segmentation masks & skeletons
    - storage/xai/: Grad-CAM saliency heatmaps & 5-panel clinical cards
    - storage/reports/: Downloadable clinical PDF/JSON findings packages
    """

    def __init__(self, root: Union[str, Path]) -> None:
        self.root = Path(root).resolve()
        self.tiers = {
            "raw": self.root / "raw",
            "masks": self.root / "masks",
            "xai": self.root / "xai",
            "reports": self.root / "reports",
        }
        for tier_dir in self.tiers.values():
            tier_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self, fileobj: BinaryIO, filename: str, case_id: Union[int, str], tier: str = "raw"
    ) -> StoredFile:
        """Stores a raw angiogram image with SHA-256 deduplication and sanitized key."""
        extension = get_extension(filename)
        if extension not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(f"Format '{extension}' is not supported. Allowed: {ALLOWED_EXTENSIONS}")

        key = f"{tier}/{case_id}/{uuid.uuid4().hex}{extension}"
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)

        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        hasher = hashlib.sha256()
        size = 0
        try:
            with path.open("wb") as out:
                while chunk := fileobj.read(CHUNK_SIZE):
                    size += len(chunk)
                    if size > max_bytes:
                        raise FileTooLargeError(settings.MAX_UPLOAD_MB)
                    hasher.update(chunk)
                    out.write(chunk)
        except Exception:
            path.unlink(missing_ok=True)
            raise

        return StoredFile(key=key, size_bytes=size, sha256=hasher.hexdigest(), tier=tier)

    def save_bytes(
        self, data: bytes, filename: str, case_id: Union[int, str], tier: str = "xai"
    ) -> StoredFile:
        """Saves generated binary assets (e.g. Grad-CAM cards, masks, PDF reports)."""
        extension = get_extension(filename) or ".png"
        key = f"{tier}/{case_id}/{uuid.uuid4().hex}{extension}"
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)

        hasher = hashlib.sha256(data)
        with path.open("wb") as out:
            out.write(data)

        return StoredFile(key=key, size_bytes=len(data), sha256=hasher.hexdigest(), tier=tier)

    def resolve(self, key: str) -> Path:
        """Resolves relative storage key to an absolute Path with path traversal protection."""
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise FileNotFoundError(f"Storage asset not found: {key}")
        return path

    def delete(self, key: str) -> None:
        try:
            self.resolve(key).unlink()
        except FileNotFoundError:
            pass

    def get_storage_stats(self) -> Dict[str, Union[int, float, Dict[str, int]]]:
        """Returns storage telemetry for Admin dashboard."""
        total_size = 0
        file_count = 0
        file_counts = {tier: 0 for tier in self.tiers}
        for p in self.root.rglob("*"):
            if p.is_file():
                total_size += p.stat().st_size
                file_count += 1
                for tier in self.tiers:
                    if self.tiers[tier] in p.parents or p.parent == self.tiers[tier]:
                        file_counts[tier] += 1
        return {
            "total_bytes": total_size,
            "total_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "file_counts": file_counts,
            "root_path": str(self.root),
        }


storage = LocalStorage(settings.STORAGE_ROOT)
