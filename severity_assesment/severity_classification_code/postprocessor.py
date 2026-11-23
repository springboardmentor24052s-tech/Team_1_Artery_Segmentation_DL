"""
StenoVision - Stenosis Bounding Box Post-Processor & NMS
========================================================
Applies Non-Maximum Suppression (NMS) and confidence filtering to merge
overlapping candidate lesion detections and extract centroids.
"""

from typing import Dict, List, Tuple
import cv2
import numpy as np
import torch
import torchvision.ops as ops


def filter_and_suppress_detections(
    boxes: np.ndarray,
    scores: np.ndarray,
    labels: np.ndarray,
    score_threshold: float = 0.25,
    nms_iou_threshold: float = 0.30,
    max_detections: int = 10,
) -> List[Dict]:
    """
    Applies score thresholding and Non-Maximum Suppression (NMS).

    Returns list of localized lesion detections:
    [{
        'bbox': [x1, y1, x2, y2],
        'centroid': (cx, cy),
        'width': w,
        'height': h,
        'confidence': score,
        'label': label_idx
    }, ...]
    """
    if len(boxes) == 0:
        return []

    # Convert to PyTorch tensors for fast NMS
    t_boxes = torch.as_tensor(boxes, dtype=torch.float32)
    t_scores = torch.as_tensor(scores, dtype=torch.float32)

    # 1. Score threshold filter
    keep_indices = torch.where(t_scores >= score_threshold)[0]
    if len(keep_indices) == 0:
        return []

    t_boxes = t_boxes[keep_indices]
    t_scores = t_scores[keep_indices]
    labels_filtered = labels[keep_indices.cpu().numpy()]

    # 2. Non-Maximum Suppression
    nms_keep = ops.nms(t_boxes, t_scores, nms_iou_threshold)
    nms_keep = nms_keep[:max_detections]

    final_detections = []
    for idx in nms_keep:
        b = t_boxes[idx].cpu().numpy().tolist()
        x1, y1, x2, y2 = [int(round(coord)) for coord in b]
        w = max(1, x2 - x1)
        h = max(1, y2 - y1)
        cx = int(x1 + w / 2.0)
        cy = int(y1 + h / 2.0)
        score = float(t_scores[idx].cpu().item())
        lbl = int(labels_filtered[idx.cpu().item()])

        final_detections.append({
            "bbox": [x1, y1, x2, y2],
            "centroid": (cx, cy),
            "width": w,
            "height": h,
            "confidence": round(score, 3),
            "label": lbl,
        })

    return final_detections

