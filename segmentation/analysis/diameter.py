"""
StenoVision - Vessel Diameter Estimation & Luminal Analysis
===========================================================
Estimates local coronary vessel diameters along the extracted centerlines using
the Euclidean Distance Transform (EDT). Computes clinical metrics:
- Reference Vessel Diameter (RVD)
- Minimum Luminal Diameter (MLD)
- Percentage Diameter Stenosis (% DS)
"""

from typing import Dict, Tuple
import cv2
import numpy as np


def compute_distance_transform(binary_mask: np.ndarray) -> np.ndarray:
    """
    Computes Euclidean Distance Transform (EDT).
    For each vessel pixel, returns the shortest distance to the nearest background pixel.
    """
    if binary_mask.dtype != np.uint8:
        binary_mask = (binary_mask > 0).astype(np.uint8) * 255
    return cv2.distanceTransform(binary_mask, cv2.DIST_L2, 5)


def estimate_vessel_diameters(
    binary_mask: np.ndarray,
    skeleton: np.ndarray,
    pixel_spacing_mm: float = 0.25,  # Typical in-plane XCA pixel spacing: ~0.2-0.3 mm
) -> Dict:
    """
    Measures local vessel diameter along the centerline points:
    Diameter = 2 * DistanceTransform
    """
    dist_map = compute_distance_transform(binary_mask)

    # Sample distances at centerline pixels
    skel_coords = np.where(skeleton > 0)
    radii_px = dist_map[skel_coords]
    diameters_px = radii_px * 2.0

    if len(diameters_px) == 0:
        return {
            "mean_diameter_px": 0.0,
            "mean_diameter_mm": 0.0,
            "min_diameter_px": 0.0,
            "min_diameter_mm": 0.0,
            "max_diameter_px": 0.0,
            "max_diameter_mm": 0.0,
            "rvd_mm": 0.0,
            "mld_mm": 0.0,
            "percent_stenosis": 0.0,
            "diameter_map": np.zeros_like(dist_map),
        }

    # Clinical reference diameter: 75th percentile of normal vessel lumen
    rvd_px = float(np.percentile(diameters_px, 75))
    # Minimum luminal diameter: 5th percentile (robust to single-pixel boundary artifacts)
    mld_px = float(np.percentile(diameters_px, 5))

    rvd_mm = rvd_px * pixel_spacing_mm
    mld_mm = mld_px * pixel_spacing_mm

    # Percent diameter stenosis: (1 - MLD / RVD) * 100
    if rvd_mm > 0:
        percent_stenosis = max(0.0, min(100.0, (1.0 - (mld_mm / rvd_mm)) * 100.0))
    else:
        percent_stenosis = 0.0

    # Build diameter overlay map on skeleton
    diameter_map = np.zeros_like(dist_map, dtype=np.float32)
    diameter_map[skel_coords] = diameters_px * pixel_spacing_mm

    return {
        "num_centerline_points": len(diameters_px),
        "mean_diameter_px": float(np.mean(diameters_px)),
        "mean_diameter_mm": float(np.mean(diameters_px) * pixel_spacing_mm),
        "median_diameter_mm": float(np.median(diameters_px) * pixel_spacing_mm),
        "min_diameter_mm": float(np.min(diameters_px) * pixel_spacing_mm),
        "max_diameter_mm": float(np.max(diameters_px) * pixel_spacing_mm),
        "rvd_mm": rvd_mm,
        "mld_mm": mld_mm,
        "percent_stenosis": float(percent_stenosis),
        "diameter_map": diameter_map,
        "distance_transform": dist_map,
    }

