"""
Sub-Team 1: Stenosis Detection Pipeline - Member 1
Module: Candidate Bounding Box & Centerline Trough Visualizer
=============================================================
Visualizes geometric caliber depression troughs and candidate bounding boxes
directly overlaid onto raw XCA coronary angiograms.
"""

from typing import List, Dict, Optional
import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def overlay_candidate_regions(
    raw_image: np.ndarray,
    candidates: List[Dict],
    output_path: Optional[str] = None,
    color_bgr: tuple = (0, 165, 255),  # Orange bounding box
) -> np.ndarray:
    """
    Draws candidate bounding boxes and centroids onto an angiogram frame.
    """
    if len(raw_image.shape) == 2:
        vis = cv2.cvtColor(raw_image, cv2.COLOR_GRAY2BGR)
    else:
        vis = raw_image.copy()

    for idx, cand in enumerate(candidates):
        x1, y1, x2, y2 = cand["bbox"]
        cx, cy = cand.get("centroid", (int((x1 + x2) / 2), int((y1 + y2) / 2)))
        pct = cand.get("estimated_pct_stenosis", 0.0)

        # Draw bounding box
        cv2.rectangle(vis, (x1, y1), (x2, y2), color_bgr, 2)

        # Draw centroid marker
        cv2.drawMarker(vis, (cx, cy), (0, 255, 0), cv2.MARKER_CROSS, 10, 2)

        # Label candidate index and percentage
        label = f"Cand #{idx+1}: {pct:.1f}%"
        cv2.putText(vis, label, (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color_bgr, 1, cv2.LINE_AA)

    if output_path:
        cv2.imwrite(str(output_path), vis)

    return vis


if __name__ == "__main__":
    # Test script with synthetic sample
    dummy_img = np.full((512, 512), 200, dtype=np.uint8)
    sample_cands = [
        {"bbox": [180, 240, 260, 310], "centroid": (220, 275), "estimated_pct_stenosis": 64.7},
        {"bbox": [310, 140, 370, 195], "centroid": (340, 167), "estimated_pct_stenosis": 32.4},
    ]
    vis_res = overlay_candidate_regions(dummy_img, sample_cands)
    print("Candidate visualizer executed successfully. Output shape:", vis_res.shape)

