"""
StenoVision - Qualitative Visualization Generator
=================================================
Renders 5-panel clinical comparison figures:
[Raw Angiogram | Ground Truth Mask | U-Net Pred | Attention U-Net Pred | Centerline & Diameter Heatmap]
"""

from pathlib import Path
from typing import Dict, Optional
import matplotlib.pyplot as plt
import numpy as np


def render_5panel_comparison(
    raw_img: np.ndarray,
    gt_mask: np.ndarray,
    unet_mask: np.ndarray,
    att_unet_mask: np.ndarray,
    skeleton: np.ndarray,
    diameter_map: np.ndarray,
    metrics_unet: Dict[str, float],
    metrics_att: Dict[str, float],
    case_name: str,
    save_path: Optional[Path] = None,
):
    fig, axes = plt.subplots(1, 5, figsize=(22, 5))

    # 1. Raw Angiogram
    axes[0].imshow(raw_img, cmap="gray")
    axes[0].set_title(f"Raw Angiogram\n({case_name})", fontweight="bold", fontsize=11)
    axes[0].axis("off")

    # 2. Ground Truth Mask
    axes[1].imshow(raw_img, cmap="gray")
    axes[1].imshow(gt_mask, cmap="Greens", alpha=0.45)
    axes[1].set_title("Ground Truth Mask\n(ARCADE SYNTAX)", fontweight="bold", fontsize=11)
    axes[1].axis("off")

    # 3. U-Net Prediction
    axes[2].imshow(raw_img, cmap="gray")
    axes[2].imshow(unet_mask, cmap="Blues", alpha=0.45)
    axes[2].set_title(
        f"Baseline U-Net\nDice: {metrics_unet['dice']:.3f} | IoU: {metrics_unet['iou']:.3f}",
        fontweight="bold",
        fontsize=11,
    )
    axes[2].axis("off")

    # 4. Attention U-Net Prediction
    axes[3].imshow(raw_img, cmap="gray")
    axes[3].imshow(att_unet_mask, cmap="autumn", alpha=0.45)
    axes[3].set_title(
        f"Attention U-Net\nDice: {metrics_att['dice']:.3f} | IoU: {metrics_att['iou']:.3f}",
        fontweight="bold",
        fontsize=11,
        color="#2B6CB0",
    )
    axes[3].axis("off")

    # 5. Centerline & Diameter Map
    axes[4].imshow(raw_img, cmap="gray")
    # Masked diameter heatmap
    masked_d = np.ma.masked_where(skeleton == 0, diameter_map)
    im = axes[4].imshow(masked_d, cmap="jet", interpolation="nearest")
    axes[4].set_title("Vessel Centerline &\nDiameter Heatmap (mm)", fontweight="bold", fontsize=11)
    axes[4].axis("off")
    plt.colorbar(im, ax=axes[4], fraction=0.046, pad=0.04)

    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=250)
        plt.close()
    else:
        plt.show()

