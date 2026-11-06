"""
StenoVision - Segmentation Evaluation Metrics
=============================================
Calculates key medical image segmentation metrics between binary predictions and ground truth:
- Dice Similarity Coefficient (DSC / F1-Score)
- Intersection over Union (IoU / Jaccard Index)
- Precision (Positive Predictive Value)
- Recall / Sensitivity (True Positive Rate)
- Specificity (True Negative Rate)
"""

from typing import Dict
import numpy as np


def compute_segmentation_metrics(pred_mask: np.ndarray, gt_mask: np.ndarray) -> Dict[str, float]:
    """
    Computes statistical confusion matrix and derived overlap metrics.
    Inputs: binary boolean or 0/255 uint8 arrays.
    """
    pred = pred_mask > 0
    gt = gt_mask > 0

    tp = float((pred & gt).sum())
    fp = float((pred & ~gt).sum())
    fn = float((~pred & gt).sum())
    tn = float((~pred & ~gt).sum())

    # Dice / F1
    dice = (2.0 * tp) / (2.0 * tp + fp + fn + 1e-7)

    # IoU / Jaccard
    iou = tp / (tp + fp + fn + 1e-7)

    # Precision
    precision = tp / (tp + fp + 1e-7)

    # Recall / Sensitivity
    recall = tp / (tp + fn + 1e-7)

    # Specificity
    specificity = tn / (tn + fp + 1e-7)

    # Accuracy
    accuracy = (tp + tn) / (tp + tn + fp + fn + 1e-7)

    return {
        "dice": float(dice),
        "iou": float(iou),
        "precision": float(precision),
        "recall": float(recall),
        "specificity": float(specificity),
        "accuracy": float(accuracy),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
    }

