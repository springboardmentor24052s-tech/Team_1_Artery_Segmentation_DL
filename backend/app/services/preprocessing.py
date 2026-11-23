"""
StenoVision - Preprocessing Pipeline Service
============================================
Provides standardized medical image preprocessing for coronary angiograms (XCA):
1. Input validation & grayscale conversion
2. Dimension standardization (512x512)
3. Contrast Limited Adaptive Histogram Equalization (CLAHE)
4. Intensity normalization ([0.0, 1.0] and z-score)
5. PyTorch tensor conversion (1, H, W)
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np
from PIL import Image

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def load_angiogram(
    image_input: Union[str, Path, Image.Image, np.ndarray],
    target_size: Optional[Tuple[int, int]] = (512, 512),
) -> np.ndarray:
    """
    Loads an angiogram from file path, PIL Image, or array and converts to 8-bit grayscale.
    Optionally resizes to target_size (width, height).
    """
    if isinstance(image_input, (str, Path)):
        path = Path(image_input)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        pil_img = Image.open(path).convert("L")
    elif isinstance(image_input, Image.Image):
        pil_img = image_input.convert("L")
    elif isinstance(image_input, np.ndarray):
        if image_input.ndim == 3:
            # If 3-channel, convert to grayscale via luminance weights
            if HAS_CV2:
                image_input = cv2.cvtColor(image_input, cv2.COLOR_BGR2GRAY if image_input.shape[2] == 3 else cv2.COLOR_RGBA2GRAY)
            else:
                image_input = np.dot(image_input[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
        if image_input.dtype != np.uint8:
            # Scale to 0-255 uint8 if float
            if image_input.max() <= 1.0:
                image_input = (image_input * 255.0).clip(0, 255).astype(np.uint8)
            else:
                image_input = image_input.clip(0, 255).astype(np.uint8)
        pil_img = Image.fromarray(image_input)
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    if target_size is not None and pil_img.size != target_size:
        pil_img = pil_img.resize(target_size, Image.Resampling.BILINEAR)

    return np.array(pil_img, dtype=np.uint8)


def apply_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
) -> np.ndarray:
    """
    Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)
    to enhance subtle lumen boundaries in coronary arteries.
    """
    if not (image.dtype == np.uint8 and image.ndim == 2):
        raise ValueError("CLAHE requires a 2D uint8 grayscale image.")

    if HAS_CV2:
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        return clahe.apply(image)
    else:
        # Fallback simple histogram equalization if cv2 unavailable
        hist, bins = np.histogram(image.flatten(), 256, [0, 256])
        cdf = hist.cumsum()
        cdf_m = np.ma.masked_equal(cdf, 0)
        cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
        cdf = np.ma.filled(cdf_m, 0).astype("uint8")
        return cdf[image]


def normalize_intensity(
    image: np.ndarray,
    mode: str = "minmax",
) -> np.ndarray:
    """
    Normalizes pixel intensities:
    - 'minmax': scales to [0.0, 1.0] float32
    - 'zscore': zero-mean, unit-variance standardization
    """
    img_float = image.astype(np.float32)

    if mode == "minmax":
        # Standard angiogram linear normalization
        return img_float / 255.0
    elif mode == "zscore":
        mean = img_float.mean()
        std = img_float.std() + 1e-7
        return (img_float - mean) / std
    else:
        raise ValueError(f"Unknown normalization mode: '{mode}'. Use 'minmax' or 'zscore'.")


def to_torch_tensor(image: np.ndarray) -> "torch.Tensor":
    """
    Converts a 2D (H, W) or 3D (H, W, C) numpy array to a PyTorch tensor (1, H, W).
    """
    if not HAS_TORCH:
        raise RuntimeError("PyTorch is required for tensor conversion.")
    if image.ndim == 2:
        tensor = torch.from_numpy(image).unsqueeze(0)  # (1, H, W)
    elif image.ndim == 3 and image.shape[2] == 1:
        tensor = torch.from_numpy(image[:, :, 0]).unsqueeze(0)
    else:
        tensor = torch.from_numpy(image).permute(2, 0, 1)
    return tensor.float()


def preprocess_angiogram(
    image_input: Union[str, Path, Image.Image, np.ndarray],
    target_size: Optional[Tuple[int, int]] = (512, 512),
    use_clahe: bool = True,
    clip_limit: float = 2.0,
    normalization: str = "minmax",
    return_tensor: bool = True,
) -> Dict[str, Union[np.ndarray, "torch.Tensor", Tuple[int, int]]]:
    """
    End-to-End Preprocessing Pipeline:
    1. Ingests and formats image to 8-bit grayscale at target_size.
    2. Applies CLAHE contrast enhancement (if enabled).
    3. Normalizes intensities according to specified mode.
    4. Converts to PyTorch tensor format (1, H, W).

    Returns a dictionary containing each intermediate and final representation.
    """
    raw_gray = load_angiogram(image_input, target_size=target_size)

    if use_clahe:
        enhanced = apply_clahe(raw_gray, clip_limit=clip_limit)
    else:
        enhanced = raw_gray.copy()

    normalized = normalize_intensity(enhanced, mode=normalization)

    result = {
        "raw_gray": raw_gray,
        "enhanced_clahe": enhanced,
        "normalized": normalized,
        "dimensions": raw_gray.shape,
    }

    if return_tensor and HAS_TORCH:
        result["tensor"] = to_torch_tensor(normalized)

    return result

