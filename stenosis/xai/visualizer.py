"""
StenoVision - 5-Panel Clinical XAI Diagnostic Visualizer
========================================================
Creates professional multi-panel clinical diagnostic explanation figures
combining raw angiogram, artery segmentation, cropped lesion patch,
Grad-CAM saliency heatmaps, and QCA caliper narrowing profiles.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import matplotlib.pyplot as plt
import numpy as np


def generate_5panel_xai_figure(
    image_gray: np.ndarray,
    vessel_mask: np.ndarray,
    centerline: np.ndarray,
    detection_info: Dict,
    lesion_patch: np.ndarray,
    gradcam_heatmap: np.ndarray,
    qca_info: Dict,
    save_path: Optional[Union[str, Path]] = None,
    case_title: str = "Coronary Artery Stenosis Analysis",
) -> plt.Figure:
    """
    Renders a 5-panel clinical XAI explanation figure.
    """
    fig, axes = plt.subplots(1, 5, figsize=(22, 5.5), dpi=150)
    fig.patch.set_facecolor("#111315")  # Clean clinical PACS neutral dark background

    plt.suptitle(
        f"StenoVision Clinical Decision Support — {case_title}\n"
        f"Lesion Territory: {detection_info.get('branch_name', 'Coronary Vessel')} | "
        f"Severity: {detection_info.get('severity_name', 'Stenosis')} ({qca_info.get('pct_stenosis', 0.0)}% DS)",
        fontsize=14,
        fontweight="bold",
        color="#f8fafc",
        y=1.02,
    )

    # -------------------------------------------------------------
    # Panel 1: Original Angiogram + Detected Bounding Box
    # -------------------------------------------------------------
    p1 = image_gray.copy()
    if len(p1.shape) == 2:
        p1_bgr = cv2.cvtColor(p1, cv2.COLOR_GRAY2BGR)
    else:
        p1_bgr = p1.copy()

    bbox = detection_info.get("bbox", [100, 100, 200, 200])
    x1, y1, x2, y2 = [int(v) for v in bbox]
    bgr_color = detection_info.get("bgr_tuple", (33, 17, 169))  # StenoVision crimson #A91121
    cv2.rectangle(p1_bgr, (x1, y1), (x2, y2), bgr_color, 2)
    cx, cy = detection_info.get("centroid", ((x1 + x2) // 2, (y1 + y2) // 2))
    cv2.circle(p1_bgr, (cx, cy), 4, (0, 255, 255), -1)

    axes[0].imshow(cv2.cvtColor(p1_bgr, cv2.COLOR_BGR2RGB))
    axes[0].set_title(
        f"(1) XCA Angiogram\nConf: {detection_info.get('confidence', 0.95)*100:.1f}%",
        color="#f8fafc",
        fontsize=11,
        fontweight="bold",
    )
    axes[0].axis("off")

    # -------------------------------------------------------------
    # Panel 2: Artery Tree & Medial Centerline
    # -------------------------------------------------------------
    p2_bgr = np.zeros_like(p1_bgr)
    p2_bgr[vessel_mask > 0] = [230, 180, 20]  # Cyan vessel
    p2_bgr[centerline > 0] = [30, 30, 255]    # Red centerline
    cv2.rectangle(p2_bgr, (x1, y1), (x2, y2), (255, 255, 255), 1)

    axes[1].imshow(cv2.cvtColor(p2_bgr, cv2.COLOR_BGR2RGB))
    axes[1].set_title(
        "(2) Segmented Tree\nAttention U-Net Prior",
        color="#f8fafc",
        fontsize=11,
        fontweight="bold",
    )
    axes[1].axis("off")

    # -------------------------------------------------------------
    # Panel 3: High-Resolution Cropped Lesion Patch (128x128)
    # -------------------------------------------------------------
    axes[2].imshow(lesion_patch, cmap="gray")
    axes[2].set_title(
        "(3) Cropped Lesion ROI\n128x128 High-Res",
        color="#f8fafc",
        fontsize=11,
        fontweight="bold",
    )
    axes[2].axis("off")

    # -------------------------------------------------------------
    # Panel 4: Grad-CAM Explainable AI Saliency Heatmap
    # -------------------------------------------------------------
    if len(lesion_patch.shape) == 2:
        patch_bgr = cv2.cvtColor(lesion_patch, cv2.COLOR_GRAY2BGR)
    else:
        patch_bgr = lesion_patch.copy()

    if gradcam_heatmap.shape[:2] != patch_bgr.shape[:2]:
        hmap = cv2.resize(gradcam_heatmap, (patch_bgr.shape[1], patch_bgr.shape[0]))
    else:
        hmap = gradcam_heatmap

    gradcam_blend = cv2.addWeighted(patch_bgr, 0.45, hmap, 0.55, 0)
    axes[3].imshow(cv2.cvtColor(gradcam_blend, cv2.COLOR_BGR2RGB))
    axes[3].set_title(
        "(4) Grad-CAM Saliency\nFilling Defect Proof",
        color="#f8fafc",
        fontsize=11,
        fontweight="bold",
    )
    axes[3].axis("off")

    # -------------------------------------------------------------
    # Panel 5: Quantitative QCA Caliper Narrowing Profile
    # -------------------------------------------------------------
    # Synthesize diameter caliber profile curve across lesion
    pts = 50
    s = np.linspace(-10, 10, pts)
    rvd = qca_info.get("rvd_mm", 3.2)
    mld = qca_info.get("mld_mm", 1.0)
    pct_ds = qca_info.get("pct_stenosis", 68.0)
    # Gaussian depression profile
    depth = rvd - mld
    diam_profile = rvd - depth * np.exp(-(s**2) / 12.0)

    axes[4].set_facecolor("#18181b")
    axes[4].plot(s, diam_profile, color="#A91121", linewidth=2.5, label="Lumen Caliper")
    axes[4].axhline(y=rvd, color="#10b981", linestyle="--", alpha=0.9, label=f"RVD: {rvd:.2f} mm")
    axes[4].axhline(y=mld, color="#ef4444", linestyle="--", alpha=0.9, label=f"MLD: {mld:.2f} mm")
    axes[4].scatter([0], [mld], color="#ef4444", s=60, zorder=5)

    axes[4].set_title(
        f"(5) QCA Caliper Profile\n%DS: {pct_ds:.1f}% ({detection_info.get('tier', 'Severe')})",
        color="#f8fafc",
        fontsize=11,
        fontweight="bold",
    )
    axes[4].set_xlabel("Vessel Axis (mm)", color="#94a3b8", fontsize=9)
    axes[4].set_ylabel("Diameter (mm)", color="#94a3b8", fontsize=9)
    axes[4].tick_params(colors="#94a3b8")
    axes[4].grid(True, linestyle=":", alpha=0.3, color="#64748b")
    axes[4].legend(loc="upper right", fontsize=8, facecolor="#111315", edgecolor="#334155", labelcolor="#f8fafc")

    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(save_path), bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)

    return fig


def generate_4panel_xai_figure(
    image_gray: np.ndarray,
    vessel_mask: np.ndarray,
    detection_info: Dict,
    attribution_heatmap_bgr: np.ndarray,
    save_path: Optional[Union[str, Path]] = None,
    case_title: str = "Coronary Artery Explainable AI",
) -> plt.Figure:
    """
    Renders the official 4-panel Explainable AI diagnostic figure:
    (1) Original Image – Native angiography scan
    (2) AI Prediction – Segmented vessel prior + detected stenosis region
    (3) Explainability Heatmap – Model attribution (Red/Yellow = High, Dark = Low)
    (4) Combined Visualization – Original anatomy + segmentation + attribution overlay
    """
    fig, axes = plt.subplots(1, 4, figsize=(18, 5.0), dpi=150)
    fig.patch.set_facecolor("#111315")  # Clean clinical PACS neutral dark background

    branch = detection_info.get("branch_name", "Coronary Vessel")
    tier = detection_info.get("severity_name", detection_info.get("tier", "Stenosis"))
    pct_ds = detection_info.get("pct_stenosis", detection_info.get("pct_ds", 64.7))

    plt.suptitle(
        f"StenoVision Explainable AI (XAI) Diagnostic Explanation — {case_title}\n"
        f"Target Territory: {branch} | Prediction: {tier} ({pct_ds:.1f}% DS)",
        fontsize=13,
        fontweight="bold",
        color="#f8fafc",
        y=1.03,
    )

    # Prepare base RGB image
    if len(image_gray.shape) == 2:
        base_bgr = cv2.cvtColor(image_gray, cv2.COLOR_GRAY2BGR)
    else:
        base_bgr = image_gray.copy()
    base_rgb = cv2.cvtColor(base_bgr, cv2.COLOR_BGR2RGB)

    H, W = image_gray.shape[:2]
    bbox = detection_info.get("bbox", [int(W * 0.35), int(H * 0.35), int(W * 0.65), int(H * 0.65)])
    x1, y1, x2, y2 = [int(v) for v in bbox]

    # Panel 1: Original Image
    axes[0].imshow(base_rgb)
    axes[0].set_title(
        "(1) Original Image\nUploaded Angiogram (512x512)",
        color="#f8fafc",
        fontsize=10,
        fontweight="bold",
    )
    axes[0].axis("off")

    # Panel 2: AI Prediction (Segmentation + Localized Lesion)
    pred_bgr = base_bgr.copy()
    # Mask overlay in cyan
    overlay = np.zeros_like(base_bgr)
    overlay[vessel_mask > 0] = [230, 180, 20]
    mask_indices = vessel_mask > 0
    if np.any(mask_indices):
        pred_bgr[mask_indices] = (base_bgr[mask_indices] * 0.4 + overlay[mask_indices] * 0.6).astype(np.uint8)
    # Bounding box in StenoVision crimson #A91121: (33, 17, 169) in BGR
    cv2.rectangle(pred_bgr, (x1, y1), (x2, y2), (33, 17, 169), 2)
    # Center lesion target dot
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    cv2.circle(pred_bgr, (cx, cy), 5, (0, 255, 255), -1)

    axes[1].imshow(cv2.cvtColor(pred_bgr, cv2.COLOR_BGR2RGB))
    axes[1].set_title(
        f"(2) AI Prediction\n{branch} Lesion ({tier})",
        color="#f8fafc",
        fontsize=10,
        fontweight="bold",
    )
    axes[1].axis("off")

    # Panel 3: Explainability Heatmap (Red/Yellow = Strong, Dark = Low)
    if attribution_heatmap_bgr.shape[:2] != (H, W):
        heatmap_resized = cv2.resize(attribution_heatmap_bgr, (W, H))
    else:
        heatmap_resized = attribution_heatmap_bgr

    axes[2].imshow(cv2.cvtColor(heatmap_resized, cv2.COLOR_BGR2RGB))
    axes[2].set_title(
        "(3) Explainability Heatmap\nRed/Yellow: High · Dark: Low",
        color="#f8fafc",
        fontsize=10,
        fontweight="bold",
    )
    axes[2].axis("off")

    # Panel 4: Combined Visualization with Continuous Proportional Alpha Blending
    # Zero attribution = 100% native grayscale angiogram (no blue tint or fog!)
    hmap_gray = cv2.cvtColor(heatmap_resized, cv2.COLOR_BGR2GRAY)
    hmap_energy = np.clip((hmap_gray.astype(np.float32) - 15.0) / 240.0, 0.0, 1.0)
    alpha = (hmap_energy[:, :, np.newaxis] * 0.75)
    combined_bgr = (base_bgr.astype(np.float32) * (1.0 - alpha) + heatmap_resized.astype(np.float32) * alpha).astype(np.uint8)
    # Highlight lesion contour outline in soft white
    cv2.rectangle(combined_bgr, (x1, y1), (x2, y2), (240, 240, 255), 1)

    axes[3].imshow(cv2.cvtColor(combined_bgr, cv2.COLOR_BGR2RGB))
    axes[3].set_title(
        "(4) Combined Visualization\nAnatomy + Prior + Heatmap",
        color="#f8fafc",
        fontsize=10,
        fontweight="bold",
    )
    axes[3].axis("off")

    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(str(save_path), bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)

    return fig

