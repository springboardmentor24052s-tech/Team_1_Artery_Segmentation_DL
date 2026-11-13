"""
StenoVision - Quantitative Coronary Angiography (QCA) Caliper Engine
====================================================================
Calculates clinical QCA metrics for localized coronary artery lesions:
- Minimum Lumen Diameter (MLD) in mm
- Reference Vessel Diameter (RVD) in mm
- Percentage Diameter Stenosis (%DS)
- Lesion Length in mm
"""

from typing import Dict, List, Optional, Tuple, Union
import cv2
import numpy as np


def compute_qca_metrics(
    binary_mask: np.ndarray,
    bbox: List[Union[int, float]],
    pixel_spacing_mm: float = 0.25,  # Typical in-plane XCA pixel resolution: 0.25 mm/px
) -> Dict:
    """
    Computes QCA metrics for a detected lesion bounding box [x1, y1, x2, y2].
    """
    x1, y1, x2, y2 = [int(round(v)) for v in bbox]
    h_img, w_img = binary_mask.shape[:2]
    x1 = max(0, min(w_img - 1, x1))
    y1 = max(0, min(h_img - 1, y1))
    x2 = max(0, min(w_img, x2))
    y2 = max(0, min(h_img, y2))

    if (x2 - x1) <= 2 or (y2 - y1) <= 2 or cv2.countNonZero(binary_mask) == 0:
        return {
            "mld_mm": 0.0,
            "rvd_mm": 0.0,
            "pct_stenosis": 0.0,
            "lesion_length_mm": 0.0,
            "is_valid": False,
        }

    # Euclidean distance transform
    dist_map = cv2.distanceTransform((binary_mask > 0).astype(np.uint8) * 255, cv2.DIST_L2, 5)

    # 1. Sample within lesion throat (bbox)
    roi_dist = dist_map[y1:y2, x1:x2]
    vessel_pts = roi_dist[roi_dist > 0]

    # 2. Sample reference normal vessel around proximal/distal margins
    margin = 15
    mx1 = max(0, x1 - margin)
    my1 = max(0, y1 - margin)
    mx2 = min(w_img, x2 + margin)
    my2 = min(h_img, y2 + margin)
    ref_roi = dist_map[my1:my2, mx1:mx2]
    ref_pts = ref_roi[ref_roi > 0]

    if len(vessel_pts) == 0:
        mld_px = 0.0
        rvd_px = float(np.percentile(ref_pts, 90) * 2.0) if len(ref_pts) > 0 else 4.0
        pct_ds = 100.0  # Apparent total cutoff / occlusion
    else:
        mld_px = float(np.min(vessel_pts) * 2.0)
        rvd_px = float(np.percentile(ref_pts, 90) * 2.0) if len(ref_pts) > 0 else float(np.max(vessel_pts) * 2.0)
        # Ensure RVD >= MLD
        rvd_px = max(rvd_px, mld_px)
        pct_ds = max(0.0, min(100.0, ((rvd_px - mld_px) / (rvd_px + 1e-6)) * 100.0))

    # Lesion length estimation along bounding box diagonal / principal dimension
    lesion_len_px = float(np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2))

    return {
        "mld_mm": round(mld_px * pixel_spacing_mm, 2),
        "rvd_mm": round(rvd_px * pixel_spacing_mm, 2),
        "pct_stenosis": round(pct_ds, 1),
        "lesion_length_mm": round(lesion_len_px * pixel_spacing_mm, 2),
        "mld_px": round(mld_px, 2),
        "rvd_px": round(rvd_px, 2),
        "is_valid": True,
    }

