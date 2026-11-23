"""
StenoVision - Segmentation Post-Processing Pipeline
===================================================
Refines raw probability predictions from deep learning models:
1. Optimal probability thresholding (T=0.50)
2. Small connected component suppression (removes noise specks < min_area px)
3. Morphological closing (bridges micro-discontinuities in thin vessel branches)
4. Topological hole filling (restores continuous arterial lumens)
"""

from typing import Dict, Tuple, Union
import cv2
import numpy as np
import scipy.ndimage as ndi


class MaskPostProcessor:
    def __init__(
        self,
        threshold: float = 0.50,
        min_component_area: int = 35,
        morph_kernel_size: int = 3,
        fill_holes: bool = True,
    ):
        self.threshold = threshold
        self.min_component_area = min_component_area
        self.morph_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (morph_kernel_size, morph_kernel_size)
        )
        self.fill_holes = fill_holes

    def clean_mask(
        self,
        prediction: np.ndarray,
    ) -> Tuple[np.ndarray, Dict[str, Union[int, float]]]:
        """
        Takes probability map [0.0, 1.0] or binary array and returns
        a refined binary mask (uint8: 0 or 255) and diagnostic stats.
        """
        # 1. Binarize by threshold
        if prediction.dtype != np.uint8:
            binary = (prediction >= self.threshold).astype(np.uint8) * 255
        else:
            binary = (prediction > 127).astype(np.uint8) * 255

        raw_vessel_pixels = int((binary > 0).sum())

        # 2. Morphological Closing: bridge small gaps in thin branches
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, self.morph_kernel)

        # 3. Hole filling: ensure continuous vessel lumen
        if self.fill_holes:
            filled = ndi.binary_fill_holes(closed > 0).astype(np.uint8) * 255
        else:
            filled = closed

        # 4. Connected component analysis to suppress noise specks
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(filled, connectivity=8)

        clean = np.zeros_like(filled)
        components_removed = 0

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= self.min_component_area:
                clean[labels == i] = 255
            else:
                components_removed += 1

        final_vessel_pixels = int((clean > 0).sum())

        stats_dict = {
            "raw_vessel_pixels": raw_vessel_pixels,
            "final_vessel_pixels": final_vessel_pixels,
            "components_removed": components_removed,
            "vessel_coverage_ratio": float(final_vessel_pixels / (clean.shape[0] * clean.shape[1])),
        }

        return clean, stats_dict


def postprocess_prediction(
    prediction: np.ndarray,
    threshold: float = 0.50,
    min_component_area: int = 35,
) -> np.ndarray:
    cleaner = MaskPostProcessor(threshold=threshold, min_component_area=min_component_area)
    cleaned, _ = cleaner.clean_mask(prediction)
    return cleaned

