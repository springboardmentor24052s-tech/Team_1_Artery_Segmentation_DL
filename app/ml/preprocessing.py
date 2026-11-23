"""Medical image upload & preprocessing engine.

Raw image -> validation -> normalization -> noise reduction -> contrast enhancement
-> ROI extraction -> model input
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field

import cv2
import numpy as np

from app.config import IMAGE_SIZE

ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".dcm", ".dicom"}


class ImageValidationError(ValueError):
    pass


@dataclass
class LoadedImage:
    image: np.ndarray                 # uint8 grayscale, original resolution
    pixel_spacing_mm: float | None    # mm per pixel if known (DICOM)
    source_format: str
    original_shape: tuple
    metadata: dict = field(default_factory=dict)


@dataclass
class PreprocessResult:
    original: np.ndarray       # uint8 HxW, resized to model size
    preprocessed: np.ndarray   # uint8 HxW, denoised + CLAHE
    model_input: np.ndarray    # float32 HxW in [0,1]  (what the network sees)
    roi_bbox: tuple            # (x0, y0, x1, y1) in model space
    pixel_spacing_mm: float | None
    scale: float               # model-pixels per original pixel
    quality: dict


def _load_dicom(data: bytes) -> LoadedImage:
    import pydicom

    ds = pydicom.dcmread(io.BytesIO(data), force=True)
    arr = ds.pixel_array.astype(np.float32)
    if arr.ndim == 3:  # cine / multi-frame -> slice selection: pick the frame with max vessel contrast
        if arr.shape[-1] in (3, 4) and arr.shape[0] > 4:
            arr = arr.mean(-1)
        else:
            scores = [float(np.std(f)) for f in arr]
            arr = arr[int(np.argmax(scores))]
    slope = float(getattr(ds, "RescaleSlope", 1) or 1)
    inter = float(getattr(ds, "RescaleIntercept", 0) or 0)
    arr = arr * slope + inter
    if str(getattr(ds, "PhotometricInterpretation", "")).upper() == "MONOCHROME1":
        arr = arr.max() - arr
    lo, hi = np.percentile(arr, [0.5, 99.5])
    img = np.clip((arr - lo) / max(hi - lo, 1e-6) * 255, 0, 255).astype(np.uint8)
    spacing = None
    for tag in ("PixelSpacing", "ImagerPixelSpacing"):
        v = getattr(ds, tag, None)
        if v is not None:
            spacing = float(v[0])
            break
    meta = {k: str(getattr(ds, k, "")) for k in ("Modality", "StudyDate", "BodyPartExamined")}
    return LoadedImage(img, spacing, "DICOM", img.shape, meta)


def load_image(data: bytes, filename: str) -> LoadedImage:
    """Validate and decode an uploaded image (PNG/JPG/TIFF/BMP or DICOM)."""
    if not data:
        raise ImageValidationError("Empty file.")
    name = filename.lower()
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    is_dicom = ext in (".dcm", ".dicom") or data[128:132] == b"DICM"
    if not is_dicom and ext not in ALLOWED_EXT:
        raise ImageValidationError(f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXT)}")
    if is_dicom:
        try:
            return _load_dicom(data)
        except Exception as exc:  # noqa: BLE001
            raise ImageValidationError(f"Invalid DICOM file: {exc}") from exc
    buf = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ImageValidationError("Could not decode image - file is corrupt or not an image.")
    if img.ndim == 3:
        img = cv2.cvtColor(img[..., :3], cv2.COLOR_BGR2GRAY)
    if img.dtype != np.uint8:
        img = cv2.normalize(img.astype(np.float32), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    h, w = img.shape
    if min(h, w) < 64:
        raise ImageValidationError(f"Image too small ({w}x{h}); minimum is 64x64.")
    return LoadedImage(img, None, ext.strip(".").upper(), img.shape, {})


def assess_quality(img: np.ndarray) -> dict:
    """Simple image-quality indicators used to raise 'image quality issue' alerts."""
    contrast = float(img.std())
    sharp = float(cv2.Laplacian(img, cv2.CV_64F).var())
    mean = float(img.mean())
    issues = []
    if contrast < 20:
        issues.append("low contrast")
    if sharp < 15:
        issues.append("blurry / low detail")
    if mean < 25 or mean > 235:
        issues.append("under/over-exposed")
    return {"contrast": round(contrast, 2), "sharpness": round(sharp, 2), "mean_intensity": round(mean, 2),
            "issues": issues, "ok": not issues}


def extract_roi(img: np.ndarray) -> tuple:
    """Bounding box of the exposed field of view (removes black collimator borders)."""
    mask = img > 10
    ys, xs = np.where(mask)
    if len(xs) < 0.2 * img.size:
        return (0, 0, img.shape[1], img.shape[0])
    return (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def preprocess(loaded: LoadedImage, size: int = IMAGE_SIZE) -> PreprocessResult:
    img = loaded.image
    h, w = img.shape
    # Resolution normalization (keeps aspect ratio with padding -> square model input)
    scale = size / max(h, w)
    nh, nw = int(round(h * scale)), int(round(w * scale))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    canvas = np.zeros((size, size), np.uint8)
    y0, x0 = (size - nh) // 2, (size - nw) // 2
    canvas[y0:y0 + nh, x0:x0 + nw] = resized
    # Noise reduction + contrast enhancement (shown to the user; model was trained on the plain image)
    den = cv2.fastNlMeansDenoising(canvas, None, h=5, templateWindowSize=7, searchWindowSize=21)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(den)
    roi = extract_roi(canvas)
    # Intensity normalization for the network
    model_input = canvas.astype(np.float32) / 255.0
    spacing = loaded.pixel_spacing_mm / scale if loaded.pixel_spacing_mm else None
    return PreprocessResult(canvas, clahe, model_input, roi, spacing, scale, assess_quality(canvas))
