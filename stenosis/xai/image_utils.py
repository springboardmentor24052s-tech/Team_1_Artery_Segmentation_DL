"""
Sub-Team 3: Explainable AI & Visualization - Member 6
Module: Multi-Modal Image Processing & Canvas Compositor
========================================================
Provides color normalization, Jet colormap alpha-blending,
and high-resolution clinical multi-panel compositing utilities.
"""

from typing import Tuple, Optional
import cv2
import numpy as np


def blend_heatmap_overlay(
    raw_gray: np.ndarray,
    heatmap_norm: np.ndarray,
    alpha: float = 0.85,
    colormap: int = cv2.COLORMAP_JET,
) -> np.ndarray:
    """
    Blends a normalized [0, 1] Grad-CAM heatmap over a grayscale angiogram patch.
    """
    if raw_gray.dtype != np.uint8:
        raw_gray = (raw_gray * 255.0).astype(np.uint8) if raw_gray.max() <= 1.0 else raw_gray.astype(np.uint8)

    h, w = raw_gray.shape[:2]
    if heatmap_norm.shape[:2] != (h, w):
        heatmap_norm = cv2.resize(heatmap_norm, (w, h), interpolation=cv2.INTER_LINEAR)

    heatmap_uint8 = np.uint8(255 * np.clip(heatmap_norm, 0.0, 1.0))
    heatmap_colored = cv2.applyColorMap(heatmap_uint8, colormap)

    raw_bgr = cv2.cvtColor(raw_gray, cv2.COLOR_GRAY2BGR) if len(raw_gray.shape) == 2 else raw_gray
    overlay = cv2.addWeighted(heatmap_colored, alpha, raw_bgr, 1.0 - alpha, 0)
    return overlay


def annotate_bounding_box(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    label: str,
    color_bgr: tuple = (0, 0, 255),
) -> np.ndarray:
    """Draws a clinical bounding box with text banner onto the image."""
    x1, y1, x2, y2 = bbox
    vis = image.copy()
    cv2.rectangle(vis, (x1, y1), (x2, y2), color_bgr, 2)
    cv2.putText(vis, label, (x1, max(18, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color_bgr, 1, cv2.LINE_AA)
    return vis

