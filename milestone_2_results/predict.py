"""
StenoVision - Milestone 2 Standalone Segmentation & Vessel Analysis Predictor
=============================================================================
This module provides ready-to-use inference using the frozen Milestone 2 trained models
(Attention U-Net or Baseline U-Net) without requiring any retraining.

Features:
- Supports both PyTorch checkpoint (.pth) and compiled TorchScript (.pt) models.
- Automatic hardware selection (CUDA GPU if available, CPU fallback).
- Built-in preprocessing (normalization, 512x512 scaling).
- Morphological post-processing (noise removal, hole filling, lumen bridging).
- Vessel structure analysis (Zhang-Suen centerline skeletonization, diameter estimation).
- Outputs binary masks, clinical color overlays, and quantitative metrics (JSON).

CLI Usage:
    python predict.py --image path/to/xca.png --output-dir ./results
    python predict.py --input-dir path/to/images/ --output-dir ./batch_results

Python API Usage:
    from predict import StenoVisionPredictor
    predictor = StenoVisionPredictor()
    result = predictor.predict("case_01.png")
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import cv2
import numpy as np
import scipy.ndimage as ndi
import torch
import torch.nn as nn

# Ensure project root is in path if imported within repository
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =====================================================================
# Fallback Minimal Model Architectures (Enables standalone execution)
# =====================================================================

class DoubleConv(nn.Module):
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class AttentionGate(nn.Module):
    def __init__(self, gate_channels: int, skip_channels: int, inter_channels: int):
        super().__init__()
        self.W_g = nn.Sequential(
            nn.Conv2d(gate_channels, inter_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(inter_channels),
        )
        self.W_x = nn.Sequential(
            nn.Conv2d(skip_channels, inter_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(inter_channels),
        )
        self.psi = nn.Sequential(
            nn.ReLU(inplace=True),
            nn.Conv2d(inter_channels, 1, kernel_size=1, bias=False),
            nn.BatchNorm2d(1),
            nn.Sigmoid(),
        )

    def forward(self, g: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        g_proj = self.W_g(g)
        x_proj = self.W_x(x)
        attention_map = self.psi(g_proj + x_proj)
        return x * attention_map


class StandaloneAttentionUNet(nn.Module):
    def __init__(self, in_channels: int = 1, out_channels: int = 1, base_features: int = 16):
        super().__init__()
        f = base_features
        self.enc1 = DoubleConv(in_channels, f)
        self.pool1 = nn.MaxPool2d(2, 2)
        self.enc2 = DoubleConv(f, f * 2)
        self.pool2 = nn.MaxPool2d(2, 2)
        self.enc3 = DoubleConv(f * 2, f * 4)
        self.pool3 = nn.MaxPool2d(2, 2)
        self.enc4 = DoubleConv(f * 4, f * 8)
        self.pool4 = nn.MaxPool2d(2, 2)

        self.bottleneck = DoubleConv(f * 8, f * 16)

        self.ag4 = AttentionGate(f * 8, f * 8, f * 4)
        self.ag3 = AttentionGate(f * 4, f * 4, f * 2)
        self.ag2 = AttentionGate(f * 2, f * 2, f)
        self.ag1 = AttentionGate(f, f, f // 2)

        self.up4 = nn.ConvTranspose2d(f * 16, f * 8, 2, 2)
        self.dec4 = DoubleConv(f * 16, f * 8)
        self.up3 = nn.ConvTranspose2d(f * 8, f * 4, 2, 2)
        self.dec3 = DoubleConv(f * 8, f * 4)
        self.up2 = nn.ConvTranspose2d(f * 4, f * 2, 2, 2)
        self.dec2 = DoubleConv(f * 4, f * 2)
        self.up1 = nn.ConvTranspose2d(f * 2, f, 2, 2)
        self.dec1 = DoubleConv(f * 2, f)

        self.out_conv = nn.Conv2d(f, out_channels, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))
        e4 = self.enc4(self.pool3(e3))

        b = self.bottleneck(self.pool4(e4))

        d4 = self.up4(b)
        e4_att = self.ag4(g=d4, x=e4)
        d4 = self.dec4(torch.cat([d4, e4_att], dim=1))

        d3 = self.up3(d4)
        e3_att = self.ag3(g=d3, x=e3)
        d3 = self.dec3(torch.cat([d3, e3_att], dim=1))

        d2 = self.up2(d3)
        e2_att = self.ag2(g=d2, x=e2)
        d2 = self.dec2(torch.cat([d2, e2_att], dim=1))

        d1 = self.up1(d2)
        e1_att = self.ag1(g=d1, x=e1)
        d1 = self.dec1(torch.cat([d1, e1_att], dim=1))

        return self.out_conv(d1)


# =====================================================================
# Post-Processing and Vessel Analysis Routines
# =====================================================================

def post_process_mask(
    prob_map: np.ndarray,
    threshold: float = 0.50,
    min_area: int = 35,
    fill_holes: bool = True,
) -> np.ndarray:
    """Refines raw probability map into clean arterial mask."""
    binary = (prob_map >= threshold).astype(np.uint8) * 255

    # 1. Morphological closing to bridge small gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # 2. Filter tiny disconnected noise specks
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    cleaned = np.zeros_like(closed)
    for lbl in range(1, num_labels):
        if stats[lbl, cv2.CC_STAT_AREA] >= min_area:
            cleaned[labels == lbl] = 255

    # 3. Fill interior lumen holes
    if fill_holes and np.any(cleaned > 0):
        binary_bool = cleaned > 0
        filled = ndi.binary_fill_holes(binary_bool)
        cleaned = (filled.astype(np.uint8)) * 255

    return cleaned


def extract_skeleton(binary_mask: np.ndarray) -> np.ndarray:
    """Extracts medial 1-px wide centerline using Zhang-Suen or morphological fallback."""
    if hasattr(cv2, "ximgproc") and hasattr(cv2.ximgproc, "thinning"):
        return cv2.ximgproc.thinning(binary_mask, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
    
    skeleton = np.zeros_like(binary_mask)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    temp = binary_mask.copy()
    while True:
        eroded = cv2.erode(temp, element)
        opened = cv2.dilate(eroded, element)
        sub = cv2.subtract(temp, opened)
        skeleton = cv2.bitwise_or(skeleton, sub)
        temp = eroded.copy()
        if cv2.countNonZero(temp) == 0:
            break
    return skeleton


def analyze_vessel_geometry(
    binary_mask: np.ndarray,
    skeleton: np.ndarray,
    pixel_spacing_mm: float = 0.25,
) -> Dict:
    """Calculates vessel diameters, bifurcations, and stenosis estimates."""
    if cv2.countNonZero(binary_mask) == 0 or cv2.countNonZero(skeleton) == 0:
        return {
            "vessel_area_px": int(np.sum(binary_mask > 0)),
            "centerline_length_px": 0,
            "bifurcations": 0,
            "endpoints": 0,
            "mean_diameter_mm": 0.0,
            "rvd_mm": 0.0,
            "mld_mm": 0.0,
            "estimated_pct_stenosis": 0.0,
        }

    # Distance transform for diameter
    dist_map = cv2.distanceTransform(binary_mask, cv2.DIST_L2, 5)
    skel_coords = np.where(skeleton > 0)
    radii_px = dist_map[skel_coords]
    diameters_px = radii_px * 2.0
    diameters_mm = diameters_px * pixel_spacing_mm

    # Topology analysis: 8-connectivity kernel
    skel_binary = (skeleton > 0).astype(np.uint8)
    kernel = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]], dtype=np.uint8)
    neighbor_count = cv2.filter2D(skel_binary, -1, kernel) * skel_binary
    endpoints = int(np.sum(neighbor_count == 1))
    bifurcations = int(np.sum(neighbor_count >= 3))

    rvd_mm = float(np.percentile(diameters_mm, 90)) if len(diameters_mm) > 0 else 0.0
    mld_mm = float(np.percentile(diameters_mm, 5)) if len(diameters_mm) > 0 else 0.0
    pct_stenosis = max(0.0, ((rvd_mm - mld_mm) / (rvd_mm + 1e-6)) * 100.0) if rvd_mm > 0 else 0.0

    return {
        "vessel_area_px": int(np.sum(binary_mask > 0)),
        "centerline_length_px": int(len(radii_px)),
        "bifurcations": bifurcations,
        "endpoints": endpoints,
        "mean_diameter_mm": round(float(np.mean(diameters_mm)), 3) if len(diameters_mm) > 0 else 0.0,
        "rvd_mm": round(rvd_mm, 3),
        "mld_mm": round(mld_mm, 3),
        "estimated_pct_stenosis": round(pct_stenosis, 2),
    }


def create_clinical_overlay(
    image_gray: np.ndarray,
    binary_mask: np.ndarray,
    skeleton: np.ndarray,
) -> np.ndarray:
    """Builds RGB clinical visualization overlay."""
    if len(image_gray.shape) == 2:
        base_bgr = cv2.cvtColor(image_gray, cv2.COLOR_GRAY2BGR)
    else:
        base_bgr = image_gray.copy()

    # Vessel mask overlay in translucent cyan (BGR: [255, 200, 0])
    mask_colored = np.zeros_like(base_bgr)
    mask_colored[binary_mask > 0] = [230, 180, 20]
    overlay = cv2.addWeighted(base_bgr, 0.70, mask_colored, 0.30, 0)

    # Artery contours in bright cyan
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(overlay, contours, -1, (255, 230, 50), 1)

    # Medial centerline in bright red
    overlay[skeleton > 0] = [30, 30, 255]

    return overlay


# =====================================================================
# Main Predictor Class
# =====================================================================

class StenoVisionPredictor:
    """
    Production-ready inference wrapper for StenoVision Milestone 2 Artery Segmentation.
    """

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
    ):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Default model location: milestone_2_results/models/best_attention_unet.pth
        if model_path is None:
            default_pth = CURRENT_DIR / "models" / "best_attention_unet.pth"
            default_traced = CURRENT_DIR / "models" / "best_attention_unet_traced.pt"
            repo_pth = PROJECT_ROOT / "segmentation" / "checkpoints" / "best_attention_unet.pth"

            if default_pth.exists():
                model_path = default_pth
            elif default_traced.exists():
                model_path = default_traced
            elif repo_pth.exists():
                model_path = repo_pth
            else:
                raise FileNotFoundError(
                    f"No trained model found. Looked in {default_pth} and {repo_pth}."
                )

        self.model_path = Path(model_path)
        self.is_traced = self.model_path.suffix.lower() == ".pt"
        self._load_model()

    def _load_model(self):
        print(f"Loading StenoVision model from: {self.model_path} onto {self.device}...")
        if self.is_traced:
            self.model = torch.jit.load(str(self.model_path), map_location=self.device)
        else:
            self.model = StandaloneAttentionUNet(in_channels=1, out_channels=1, base_features=16)
            checkpoint = torch.load(self.model_path, map_location=self.device)
            state_dict = checkpoint["model_state_dict"] if "model_state_dict" in checkpoint else checkpoint
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)

        self.model.eval()
        print("Model loaded and initialized in eval mode.")

    def preprocess(self, image_input: Union[str, Path, np.ndarray]) -> Tuple[torch.Tensor, np.ndarray, Tuple[int, int]]:
        """Loads and normalizes image to [1, 1, 512, 512] float tensor."""
        if isinstance(image_input, (str, Path)):
            img = cv2.imread(str(image_input), cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise FileNotFoundError(f"Could not load image: {image_input}")
        elif isinstance(image_input, np.ndarray):
            if len(image_input.shape) == 3:
                img = cv2.cvtColor(image_input, cv2.COLOR_BGR2GRAY)
            else:
                img = image_input.copy()
        else:
            raise TypeError("image_input must be file path or numpy array.")

        orig_shape = img.shape[:2]

        # Resize to model input shape (512x512)
        if orig_shape != (512, 512):
            img_resized = cv2.resize(img, (512, 512), interpolation=cv2.INTER_LINEAR)
        else:
            img_resized = img

        # Min-max normalization
        img_float = img_resized.astype(np.float32)
        i_min, i_max = img_float.min(), img_float.max()
        norm_img = (img_float - i_min) / (i_max - i_min + 1e-8)

        # Tensor conversion [1, 1, 512, 512]
        tensor = torch.from_numpy(norm_img).unsqueeze(0).unsqueeze(0).to(self.device)
        return tensor, img_resized, orig_shape

    @torch.no_grad()
    def predict(
        self,
        image_input: Union[str, Path, np.ndarray],
        threshold: float = 0.50,
        return_analysis: bool = True,
    ) -> Dict:
        """
        Executes end-to-end inference on a single image.

        Returns dictionary with:
        - raw_probability: float array [512, 512]
        - clean_mask: uint8 binary mask [512, 512] (0 or 255)
        - skeleton: uint8 centerline mask [512, 512]
        - overlay_bgr: uint8 BGR image with clinical overlay
        - vessel_metrics: dictionary of quantitative vascular properties
        - latency_ms: inference time in milliseconds
        """
        tensor, img_512, orig_shape = self.preprocess(image_input)

        start_time = time.perf_counter()
        logits = self.model(tensor)
        probs = torch.sigmoid(logits)
        if torch.cuda.is_available() and self.device.type == "cuda":
            torch.cuda.synchronize()
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        prob_map = probs.squeeze().cpu().numpy()
        clean_mask = post_process_mask(prob_map, threshold=threshold)
        skeleton = extract_skeleton(clean_mask)

        vessel_metrics = analyze_vessel_geometry(clean_mask, skeleton) if return_analysis else {}
        overlay_bgr = create_clinical_overlay(img_512, clean_mask, skeleton)

        return {
            "probability_map": prob_map,
            "clean_mask": clean_mask,
            "skeleton": skeleton,
            "overlay_bgr": overlay_bgr,
            "vessel_metrics": vessel_metrics,
            "latency_ms": round(latency_ms, 2),
            "original_shape": orig_shape,
        }


# =====================================================================
# CLI Driver
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description="StenoVision Zero-Retraining Inference CLI")
    parser.add_argument("--image", type=str, help="Path to single input XCA image.")
    parser.add_argument("--input-dir", type=str, help="Directory of images to batch process.")
    parser.add_argument("--output-dir", type=str, default="./predictions", help="Directory to save outputs.")
    parser.add_argument("--model-path", type=str, default=None, help="Path to .pth checkpoint or .pt traced model.")
    parser.add_argument("--device", type=str, default=None, help="'cuda' or 'cpu'.")
    parser.add_argument("--threshold", type=float, default=0.50, help="Probability threshold (default: 0.50).")

    args = parser.parse_args()

    if not args.image and not args.input_dir:
        parser.print_help()
        print("\nError: Please provide either --image or --input-dir.")
        sys.exit(1)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    predictor = StenoVisionPredictor(model_path=args.model_path, device=args.device)

    # Collect images
    image_paths = []
    if args.image:
        image_paths.append(Path(args.image))
    if args.input_dir:
        in_p = Path(args.input_dir)
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            image_paths.extend(list(in_p.glob(ext)))

    print(f"Processing {len(image_paths)} image(s)...")
    summary = []

    for idx, path in enumerate(image_paths, 1):
        stem = path.stem
        res = predictor.predict(path, threshold=args.threshold)

        # Save binary mask
        mask_path = out_dir / f"{stem}_pred_mask.png"
        cv2.imwrite(str(mask_path), res["clean_mask"])

        # Save skeleton
        skel_path = out_dir / f"{stem}_centerline.png"
        cv2.imwrite(str(skel_path), res["skeleton"])

        # Save overlay
        overlay_path = out_dir / f"{stem}_overlay.png"
        cv2.imwrite(str(overlay_path), res["overlay_bgr"])

        # Save metrics
        meta = {
            "image": str(path),
            "inference_latency_ms": res["latency_ms"],
            "vessel_metrics": res["vessel_metrics"],
        }
        json_path = out_dir / f"{stem}_metrics.json"
        with open(json_path, "w") as f:
            json.dump(meta, f, indent=2)

        summary.append(meta)
        print(
            f"[{idx}/{len(image_paths)}] {stem}: latency={res['latency_ms']}ms, "
            f"vessel_px={res['vessel_metrics'].get('vessel_area_px', 0)}, "
            f"mean_diam={res['vessel_metrics'].get('mean_diameter_mm', 0.0)}mm, "
            f"est_stenosis={res['vessel_metrics'].get('estimated_pct_stenosis', 0.0)}%"
        )

    summary_file = out_dir / "batch_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nCompleted! All outputs and summary saved to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()

