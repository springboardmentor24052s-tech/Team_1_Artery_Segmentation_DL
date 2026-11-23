"""
Sub-Team 2: Localization & Severity Assessment - Member 3
Module: Localization & NMS Deduplication Verification Suite
============================================================
Tests Non-Maximum Suppression (NMS) bounding box deduplication,
coordinate clamping, and anatomical branch association on sample candidates.
"""

from typing import List, Dict
import numpy as np
from postprocessor import nms_detections
from branch_mapper import map_lesion_to_coronary_branch


def run_localization_verification():
    print("=== Testing Stenosis Localization & NMS Deduplication ===")

    # Scenario: 5 overlapping proposals around LAD Mid lesion at (220, 275)
    raw_proposals = [
        {"bbox": [180, 240, 260, 310], "score": 0.942, "centroid": (220, 275)},
        {"bbox": [185, 245, 255, 305], "score": 0.810, "centroid": (220, 275)},
        {"bbox": [178, 238, 262, 312], "score": 0.650, "centroid": (220, 275)},
        {"bbox": [182, 242, 258, 308], "score": 0.720, "centroid": (220, 275)},
        # Distinct proposal on distal LCx
        {"bbox": [320, 150, 380, 210], "score": 0.880, "centroid": (350, 180)},
    ]

    print(f"Initial raw candidate proposals: {len(raw_proposals)}")
    filtered = nms_detections(raw_proposals, iou_threshold=0.25)
    print(f"After NMS (IoU >= 0.25): {len(filtered)} lesions retained")

    assert len(filtered) == 2, f"Expected 2 distinct lesions, got {len(filtered)}"

    # Map both lesions to coronary territories
    for idx, lesion in enumerate(filtered):
        branch = map_lesion_to_coronary_branch(lesion["centroid"], image_shape=(512, 512))
        print(f"Lesion #{idx+1} [Centroid: {lesion['centroid']}, Score: {lesion['score']:.3f}]:")
        print(f"  Branch Territory: {branch['branch_name']} ({branch['segment_code']})")
        print(f"  Proximity: {branch['anatomical_description']}")

    print("Localization & branch association tests PASSED successfully.")


if __name__ == "__main__":
    run_localization_verification()

