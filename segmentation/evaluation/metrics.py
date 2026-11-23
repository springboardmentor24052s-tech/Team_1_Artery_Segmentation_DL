"""
StenoVision - Segmentation Evaluation Metrics
=============================================
Calculates key medical image segmentation metrics between binary predictions and ground truth:
- Dice Similarity Coefficient (DSC / F1-Score)
- Intersection over Union (IoU / Jaccard Index)
- Pixel Accuracy
- Precision (Positive Predictive Value)
- Recall / Sensitivity (True Positive Rate)
- Specificity (True Negative Rate)
- Hausdorff Distance (HD)
- Average Surface Distance (ASD)
"""

from typing import Dict, Tuple
import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial.distance import directed_hausdorff


def extract_boundary_points(mask: np.ndarray) -> np.ndarray:
    """Extracts boundary (x, y) coordinates of a binary mask."""
    binary = (mask > 0).astype(np.uint8)
    if binary.sum() == 0:
        return np.zeros((0, 2), dtype=np.float32)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    eroded = cv2.erode(binary, kernel)
    boundary = binary - eroded
    coords = np.column_stack(np.where(boundary > 0))  # (row, col)
    return coords.astype(np.float32)


def compute_hausdorff_distance(
    pred_mask: np.ndarray, gt_mask: np.ndarray, spacing_mm: float = 0.20
) -> Tuple[float, float]:
    """
    Computes bidirectional Hausdorff Distance between predicted and GT vessel contours.
    Returns: (hd_pixels, hd_mm)
    """
    pred_pts = extract_boundary_points(pred_mask)
    gt_pts = extract_boundary_points(gt_mask)

    if len(pred_pts) == 0 or len(gt_pts) == 0:
        return 0.0, 0.0

    d_pred_gt = directed_hausdorff(pred_pts, gt_pts)[0]
    d_gt_pred = directed_hausdorff(gt_pts, pred_pts)[0]
    hd_px = float(max(d_pred_gt, d_gt_pred))
    hd_mm = float(hd_px * spacing_mm)
    return hd_px, hd_mm


def compute_average_surface_distance(
    pred_mask: np.ndarray, gt_mask: np.ndarray, spacing_mm: float = 0.20
) -> Tuple[float, float]:
    """
    Computes bidirectional Average Surface Distance (ASD) between boundaries.
    Returns: (asd_pixels, asd_mm)
    """
    pred_binary = pred_mask > 0
    gt_binary = gt_mask > 0

    pred_pts = extract_boundary_points(pred_mask)
    gt_pts = extract_boundary_points(gt_mask)

    if len(pred_pts) == 0 or len(gt_pts) == 0:
        return 0.0, 0.0

    # Distance transforms from contours
    dt_gt = distance_transform_edt(~(extract_boundary_points(gt_mask).shape[0] > 0 and (gt_mask > 0)))
    # Compute Euclidean distance from each pred boundary point to gt boundary
    # Extract boundary masks
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    pred_boundary = (pred_binary.astype(np.uint8) - cv2.erode(pred_binary.astype(np.uint8), kernel)) > 0
    gt_boundary = (gt_binary.astype(np.uint8) - cv2.erode(gt_binary.astype(np.uint8), kernel)) > 0

    if pred_boundary.sum() == 0 or gt_boundary.sum() == 0:
        return 0.0, 0.0

    dt_gt = distance_transform_edt(~gt_boundary)
    dt_pred = distance_transform_edt(~pred_boundary)

    dist_pred_to_gt = dt_gt[pred_boundary]
    dist_gt_to_pred = dt_pred[gt_boundary]

    asd_px = float((dist_pred_to_gt.sum() + dist_gt_to_pred.sum()) / (len(dist_pred_to_gt) + len(dist_gt_to_pred) + 1e-7))
    asd_mm = float(asd_px * spacing_mm)
    return asd_px, asd_mm


def compute_segmentation_metrics(
    pred_mask: np.ndarray,
    gt_mask: np.ndarray,
    compute_distances: bool = False,
    spacing_mm: float = 0.20,
) -> Dict[str, float]:
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

    res = {
        "dice": float(dice),
        "iou": float(iou),
        "precision": float(precision),
        "recall": float(recall),
        "sensitivity": float(recall),
        "specificity": float(specificity),
        "accuracy": float(accuracy),
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
    }

    if compute_distances:
        hd_px, hd_mm = compute_hausdorff_distance(pred_mask, gt_mask, spacing_mm)
        asd_px, asd_mm = compute_average_surface_distance(pred_mask, gt_mask, spacing_mm)
        res["hausdorff_distance_px"] = round(hd_px, 2)
        res["hausdorff_distance_mm"] = round(hd_mm, 2)
        res["average_surface_distance_px"] = round(asd_px, 2)
        res["average_surface_distance_mm"] = round(asd_mm, 2)

    return res

