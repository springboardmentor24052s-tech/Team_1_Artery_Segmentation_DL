"""
StenoVision - Vessel Centerline & Topological Skeleton Analysis
===============================================================
Extracts 1-pixel wide medial centerlines of segmented coronary arteries using
the Zhang-Suen thinning algorithm (cv2.ximgproc.thinning), and detects vascular
topological features (branch points / bifurcations and terminal endpoints).
"""

from typing import Dict, List, Tuple
import cv2
import numpy as np


def extract_centerline(binary_mask: np.ndarray) -> np.ndarray:
    """
    Applies Zhang-Suen morphological thinning to extract a 1-pixel wide medial skeleton.
    Input: uint8 binary mask (255 for vessel, 0 for background).
    Output: uint8 skeleton mask (255 for centerline pixels, 0 for background).
    """
    if binary_mask.dtype != np.uint8:
        binary_mask = (binary_mask > 0).astype(np.uint8) * 255

    # Check if cv2.ximgproc thinning is available
    if hasattr(cv2, "ximgproc") and hasattr(cv2.ximgproc, "thinning"):
        skeleton = cv2.ximgproc.thinning(binary_mask, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
    else:
        # Morphological skeletonization fallback
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


def analyze_vascular_topology(skeleton: np.ndarray) -> Dict:
    """
    Analyzes the 8-connected neighborhood of each centerline pixel to identify:
    - Endpoints (degree == 1)
    - Continuation points (degree == 2)
    - Bifurcations / Branch points (degree >= 3)
    """
    skel_bool = skeleton > 0
    h, w = skeleton.shape

    # 3x3 neighbor summation kernel excluding center pixel
    kernel = np.array([
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]
    ], dtype=np.uint8)

    neighbor_count = cv2.filter2D((skel_bool).astype(np.uint8), -1, kernel)

    # Filter to skeleton pixels only
    endpoints_mask = (neighbor_count == 1) & skel_bool
    continuations_mask = (neighbor_count == 2) & skel_bool
    branch_points_mask = (neighbor_count >= 3) & skel_bool

    # Coordinates (y, x)
    endpoints = list(zip(*np.where(endpoints_mask)))
    branch_points = list(zip(*np.where(branch_points_mask)))

    return {
        "skeleton": skeleton,
        "total_centerline_pixels": int(skel_bool.sum()),
        "endpoints": endpoints,
        "num_endpoints": len(endpoints),
        "branch_points": branch_points,
        "num_branch_points": len(branch_points),
    }

