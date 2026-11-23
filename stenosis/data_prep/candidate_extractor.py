"""
StenoVision - Geometric Candidate Region Extractor via Caliper Narrowing
========================================================================
Extracts stenosis candidate regions along coronary arterial centerlines
by analyzing focal lumen caliber depressions relative to reference diameters.
"""

from typing import Dict, List, Tuple
import cv2
import numpy as np


def extract_medial_centerline(binary_mask: np.ndarray) -> np.ndarray:
    """Extracts 1-pixel medial centerline using Zhang-Suen morphological thinning."""
    if binary_mask.dtype != np.uint8:
        binary_mask = (binary_mask > 0).astype(np.uint8) * 255

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


def extract_stenosis_candidates_from_mask(
    binary_mask: np.ndarray,
    narrowing_threshold: float = 0.30,  # At least 30% local caliber drop
    min_lesion_length_px: int = 5,
    margin_px: int = 16,
    pixel_spacing_mm: float = 0.25,
) -> List[Dict]:
    """
    Analyzes vessel diameter along centerlines to extract candidate stenosis bounding boxes.

    Returns list of dicts:
    [{
        'bbox': [x1, y1, x2, y2],
        'centroid': (cx, cy),
        'mld_mm': float,
        'rvd_mm': float,
        'estimated_pct_stenosis': float,
        'candidate_type': 'geometric_caliper'
    }, ...]
    """
    if cv2.countNonZero(binary_mask) == 0:
        return []

    skeleton = extract_medial_centerline(binary_mask)
    if cv2.countNonZero(skeleton) == 0:
        return []

    # Distance transform: local radius
    dist_map = cv2.distanceTransform((binary_mask > 0).astype(np.uint8) * 255, cv2.DIST_L2, 5)
    diam_map = dist_map * 2.0  # Local diameter in pixels

    skel_pts = np.column_stack(np.where(skeleton > 0))  # (y, x) coordinates

    # Compute global reference vessel diameter (85th percentile of diameters on centerline)
    skel_diams = diam_map[skel_pts[:, 0], skel_pts[:, 1]]
    if len(skel_diams) == 0:
        return []

    rvd_global_px = float(np.percentile(skel_diams, 85))
    if rvd_global_px < 3.0:  # Noise vessel
        return []

    # Mark points where diameter drops significantly below reference
    narrowing_mask = np.zeros_like(skeleton)
    for idx, (y, x) in enumerate(skel_pts):
        d = skel_diams[idx]
        if d > 0 and (rvd_global_px - d) / rvd_global_px >= narrowing_threshold:
            narrowing_mask[y, x] = 255

    # Group contiguous narrowing pixels into candidate lesions using morphological dilation
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_narrowing = cv2.dilate(narrowing_mask, kernel, iterations=2)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated_narrowing, connectivity=8)

    candidates = []
    h_img, w_img = binary_mask.shape[:2]

    for lbl in range(1, num_labels):
        area = stats[lbl, cv2.CC_STAT_AREA]
        if area < min_lesion_length_px:
            continue

        x = stats[lbl, cv2.CC_STAT_LEFT]
        y = stats[lbl, cv2.CC_STAT_TOP]
        w = stats[lbl, cv2.CC_STAT_WIDTH]
        h = stats[lbl, cv2.CC_STAT_HEIGHT]
        cx, cy = int(centroids[lbl][0]), int(centroids[lbl][1])

        # Expand box with margin
        x1 = max(0, x - margin_px)
        y1 = max(0, y - margin_px)
        x2 = min(w_img - 1, x + w + margin_px)
        y2 = min(h_img - 1, y + h + margin_px)

        # Measure local MLD and RVD inside the expanded bounding box
        roi_dist = dist_map[y1:y2, x1:x2]
        vessel_d = roi_dist[roi_dist > 0] * 2.0

        if len(vessel_d) > 0:
            mld_px = float(np.min(vessel_d))
            rvd_local_px = float(np.percentile(vessel_d, 90))
            pct_ds = max(0.0, ((rvd_local_px - mld_px) / (rvd_local_px + 1e-6)) * 100.0)
        else:
            mld_px = 0.0
            rvd_local_px = rvd_global_px
            pct_ds = 0.0

        candidates.append({
            "bbox": [x1, y1, x2, y2],
            "centroid": (cx, cy),
            "mld_mm": round(mld_px * pixel_spacing_mm, 2),
            "rvd_mm": round(rvd_local_px * pixel_spacing_mm, 2),
            "estimated_pct_stenosis": round(pct_ds, 1),
            "candidate_type": "geometric_caliper",
        })

    return candidates

