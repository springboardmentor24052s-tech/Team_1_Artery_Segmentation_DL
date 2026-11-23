"""
StenoVision - Standalone Preprocessing Pipeline & CLI
======================================================
Usage:
    python pipeline.py --input <path_to_angiogram> --output <output_dir>
"""

import argparse
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
    if isinstance(image_input, (str, Path)):
        path = Path(image_input)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        pil_img = Image.open(path).convert("L")
    elif isinstance(image_input, Image.Image):
        pil_img = image_input.convert("L")
    elif isinstance(image_input, np.ndarray):
        if image_input.ndim == 3:
            if HAS_CV2:
                image_input = cv2.cvtColor(image_input, cv2.COLOR_BGR2GRAY if image_input.shape[2] == 3 else cv2.COLOR_RGBA2GRAY)
            else:
                image_input = np.dot(image_input[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
        if image_input.dtype != np.uint8:
            if image_input.max() <= 1.0:
                image_input = (image_input * 255.0).clip(0, 255).astype(np.uint8)
            else:
                image_input = image_input.clip(0, 255).astype(np.uint8)
        pil_img = Image.fromarray(image_input)
    else:
        raise TypeError(f"Unsupported image type: {type(image_input)}")

    if target_size is not None and pil_img.size != target_size:
        pil_img = pil_img.resize(target_size, Image.Resampling.BILINEAR)

    return np.array(pil_img, dtype=np.uint8)


def apply_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
) -> np.ndarray:
    if HAS_CV2:
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        return clahe.apply(image)
    else:
        hist, bins = np.histogram(image.flatten(), 256, [0, 256])
        cdf = hist.cumsum()
        cdf_m = np.ma.masked_equal(cdf, 0)
        cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
        cdf = np.ma.filled(cdf_m, 0).astype("uint8")
        return cdf[image]


def normalize_intensity(image: np.ndarray, mode: str = "minmax") -> np.ndarray:
    img_float = image.astype(np.float32)
    if mode == "minmax":
        return img_float / 255.0
    elif mode == "zscore":
        mean = img_float.mean()
        std = img_float.std() + 1e-7
        return (img_float - mean) / std
    else:
        raise ValueError(f"Unknown mode '{mode}'")


def to_torch_tensor(image: np.ndarray) -> "torch.Tensor":
    if not HAS_TORCH:
        raise RuntimeError("PyTorch is not installed.")
    if image.ndim == 2:
        return torch.from_numpy(image).unsqueeze(0).float()
    return torch.from_numpy(image).permute(2, 0, 1).float()


def preprocess_angiogram(
    image_input: Union[str, Path, Image.Image, np.ndarray],
    target_size: Optional[Tuple[int, int]] = (512, 512),
    use_clahe: bool = True,
    clip_limit: float = 2.0,
    normalization: str = "minmax",
    return_tensor: bool = True,
) -> Dict[str, Union[np.ndarray, "torch.Tensor", Tuple[int, int]]]:
    raw_gray = load_angiogram(image_input, target_size=target_size)
    enhanced = apply_clahe(raw_gray, clip_limit=clip_limit) if use_clahe else raw_gray.copy()
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StenoVision Preprocessing CLI")
    parser.add_argument("--input", type=str, help="Path to input angiogram image")
    parser.add_argument("--output", type=str, default="preprocessed_output", help="Directory to save preprocessed results")
    args = parser.parse_args()

    if args.input:
        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        res = preprocess_angiogram(args.input)
        Image.fromarray(res["raw_gray"]).save(out_dir / "1_raw_gray.png")
        Image.fromarray(res["enhanced_clahe"]).save(out_dir / "2_clahe_enhanced.png")
        norm_view = (res["normalized"] * 255.0).astype(np.uint8)
        Image.fromarray(norm_view).save(out_dir / "3_normalized_view.png")
        print(f"Preprocessed output successfully saved to {out_dir}")
    else:
        print("Self-test: creating dummy 512x512 angiogram and verifying pipeline...")
        dummy = np.random.randint(40, 220, (512, 512), dtype=np.uint8)
        res = preprocess_angiogram(dummy)
        print("Raw shape:", res["raw_gray"].shape, "dtype:", res["raw_gray"].dtype)
        print("Enhanced shape:", res["enhanced_clahe"].shape)
        print("Normalized range:", (res["normalized"].min(), res["normalized"].max()))
        if "tensor" in res:
            print("Tensor shape:", res["tensor"].shape, "dtype:", res["tensor"].dtype)
        print("Self-test PASSED!")

