"""Encryption at rest for patient images and analysis results.

Uses Fernet (AES-128-CBC with HMAC-SHA256) from the `cryptography` package. The key comes from
DATA_ENCRYPTION_KEY, which production deployments should load from a secret manager. If it is not set, a random
key is generated once and stored in storage/secret.key with owner-only permissions.
"""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.config import DATA_ENCRYPTION_KEY, RESULTS_DIR, STORAGE_DIR, UPLOAD_DIR

log = logging.getLogger("artery.retention")
KEY_FILE = STORAGE_DIR / "secret.key"
ENC_SUFFIX = ".enc"
_fernet: Fernet | None = None


def _load_key() -> bytes:
    if DATA_ENCRYPTION_KEY:
        return DATA_ENCRYPTION_KEY.encode()
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes().strip()
    key = Fernet.generate_key()
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(key)
    return key


def fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_load_key())
    return _fernet


def write_protected(path: Path, data: bytes) -> Path:
    """Encrypt `data` into `<path>.enc`. The plain file is never written."""
    path = Path(path)
    target = path if path.name.endswith(ENC_SUFFIX) else path.with_name(path.name + ENC_SUFFIX)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(fernet().encrypt(data))
    return target


def read_protected(path: Path) -> bytes:
    """Read and decrypt a `.enc` file. Plain files (written before encryption was enabled) are returned as-is."""
    path = Path(path)
    raw = path.read_bytes()
    if path.name.endswith(ENC_SUFFIX):
        try:
            return fernet().decrypt(raw)
        except InvalidToken as exc:
            raise ValueError(f"Cannot decrypt {path.name}: the data key does not match") from exc
    return raw


def resolve(directory: Path, name: str) -> Path | None:
    """Locate `name` inside `directory`, preferring the encrypted copy."""
    for candidate in (Path(directory) / (name + ENC_SUFFIX), Path(directory) / name):
        if candidate.exists():
            return candidate
    return None


def encrypt_tree(directory: Path) -> int:
    """Encrypt every PNG the pipeline wrote into `directory` and delete the plain copies."""
    count = 0
    for png in sorted(Path(directory).glob("*.png")):
        write_protected(png, png.read_bytes())
        png.unlink()
        count += 1
    return count


def _inside(path: Path, root: Path) -> bool:
    """True only when `path` resolves to a location inside `root` (guards against stray or malicious paths)."""
    try:
        return Path(path).resolve().is_relative_to(Path(root).resolve())
    except (OSError, ValueError):
        return False


def remove_stored_files(files: list[Path], folders: list[Path]) -> tuple[int, int]:
    """Delete uploaded images and analysis result folders when a patient or case is deleted.

    Call this AFTER the database commit: if the database delete fails, nothing on disk is removed.
    Only paths inside the uploads and results folders are touched. Returns (removed, failed).
    """
    removed = failed = 0
    for f in files:
        if not _inside(f, UPLOAD_DIR):
            log.warning("refusing to delete a file outside the uploads folder: %s", f)
            failed += 1
            continue
        try:
            if f.exists():
                f.unlink()
                removed += 1
        except OSError:
            log.exception("could not delete stored image %s", f)
            failed += 1
    for d in folders:
        if not _inside(d, RESULTS_DIR):
            log.warning("refusing to delete a folder outside the results folder: %s", d)
            failed += 1
            continue
        try:
            if d.exists():
                shutil.rmtree(d)
                removed += 1
        except OSError:
            log.exception("could not delete result folder %s", d)
            failed += 1
    return removed, failed
