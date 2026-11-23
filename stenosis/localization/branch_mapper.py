"""
StenoVision - Anatomical Coronary Branch Association
====================================================
Maps localized lesion centroids to anatomical coronary arterial territories
(LAD, LCx, RCA, LM) using coronary vascular geometry and spatial distribution.
"""

from typing import Dict, Tuple


def map_lesion_to_coronary_branch(
    centroid: Tuple[int, int],
    img_shape: Tuple[int, int] = (512, 512),
) -> Dict[str, str]:
    """
    Infers the affected coronary artery branch from lesion centroid (cx, cy).
    """
    cx, cy = centroid
    h, w = img_shape

    # Standard anterior/oblique angiographic projection quadrant heuristics:
    # Top-center: Left Main / Proximal Bifurcation
    # Left-mid to bottom: Left Anterior Descending (LAD)
    # Upper-right to mid-lateral: Left Circumflex (LCx)
    # Right C-shaped curve: Right Coronary Artery (RCA)
    rel_x = cx / w
    rel_y = cy / h

    if rel_y < 0.25 and 0.35 <= rel_x <= 0.65:
        branch_name = "Left Main Trunk (LMCA)"
        segment_code = "LM-Ostial/Bifurcation"
    elif rel_x < 0.52 and rel_y >= 0.25:
        if rel_y < 0.50:
            branch_name = "Left Anterior Descending (LAD - Proximal)"
            segment_code = "LAD-1"
        elif rel_y < 0.75:
            branch_name = "Left Anterior Descending (LAD - Mid)"
            segment_code = "LAD-2"
        else:
            branch_name = "Left Anterior Descending (LAD - Distal / Apical)"
            segment_code = "LAD-3"
    elif rel_x >= 0.52 and rel_y < 0.60:
        if rel_x < 0.75:
            branch_name = "Left Circumflex Artery (LCx - Proximal)"
            segment_code = "LCx-1"
        else:
            branch_name = "Obtuse Marginal Branch (OM)"
            segment_code = "OM-Branch"
    else:
        if rel_y < 0.50:
            branch_name = "Right Coronary Artery (RCA - Proximal)"
            segment_code = "RCA-1"
        else:
            branch_name = "Right Coronary Artery (RCA - Mid/Distal PDA)"
            segment_code = "RCA-2"

    return {
        "branch_name": branch_name,
        "segment_code": segment_code,
    }

