"""
StenoVision - Comparative Model Evaluation & Benchmark Engine
=============================================================
Evaluates Baseline U-Net and Advanced Attention U-Net on the held-out test split (300 images):
- Calculates Dice, IoU, Precision, Recall, Specificity
- Measures inference latency (ms / FPS)
- Generates 5-panel clinical qualitative comparisons
- Saves results to evaluation/comparison_results.json
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent
for p in [str(WORKSPACE_ROOT), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Support UTF-8 in Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import cv2
import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader
from tqdm import tqdm

from StenoVision.segmentation.analysis.centerline import analyze_vascular_topology, extract_centerline
from StenoVision.segmentation.analysis.diameter import estimate_vessel_diameters
from StenoVision.segmentation.evaluation.metrics import compute_segmentation_metrics
from StenoVision.segmentation.evaluation.visualizer import render_5panel_comparison
from StenoVision.segmentation.models import AttentionUNet, UNet
from StenoVision.segmentation.postprocessing.cleaner import postprocess_prediction
from StenoVision.segmentation.training.dataset import ArterySegmentationDataset


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MASKS_ROOT = PROJECT_ROOT / "data" / "masks"
CHECKPOINT_DIR = PROJECT_ROOT / "segmentation" / "checkpoints"
EVAL_DIR = PROJECT_ROOT / "segmentation" / "evaluation"
PLOTS_DIR = EVAL_DIR / "plots"


def load_model(model_cls, weights_path: Path, device: torch.device):
    model = model_cls(in_channels=1, out_channels=1).to(device)
    if weights_path.exists():
        ckpt = torch.load(weights_path, map_location=device)
        state_dict = ckpt["model_state_dict"] if "model_state_dict" in ckpt else ckpt
        model.load_state_dict(state_dict)
        print(f"Loaded weights from {weights_path} (epoch {ckpt.get('epoch', 'N/A')}, best val dice {ckpt.get('val_dice', 0):.4f})")
    else:
        print(f"Warning: Weights not found at {weights_path}. Model using initialized weights.")
    model.eval()
    return model


def run_evaluation():
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("=" * 75)
    print("StenoVision: Comparative Model Evaluation on ARCADE Test Split (300 Images)")
    print(f"Hardware Device: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})")
    print("=" * 75)

    test_manifest = MASKS_ROOT / "test_manifest.json"
    test_ds = ArterySegmentationDataset(test_manifest, augment=False, use_clahe=True)
    test_loader = DataLoader(test_ds, batch_size=1, shuffle=False)

    unet_path = CHECKPOINT_DIR / "best_unet.pth"
    att_path = CHECKPOINT_DIR / "best_attention_unet.pth"

    model_unet = load_model(UNet, unet_path, device)
    model_att = load_model(AttentionUNet, att_path, device)

    metrics_unet_list = []
    metrics_att_list = []
    latencies_unet = []
    latencies_att = []

    print("\nRunning test inference across 300 held-out images...")
    for idx, (img_t, mask_t, meta) in enumerate(tqdm(test_loader)):
        img_t = img_t.to(device)
        gt_np = mask_t.squeeze().cpu().numpy().astype(np.uint8)

        # 1. Inference U-Net
        t0 = time.perf_counter()
        with torch.no_grad():
            out_unet = model_unet(img_t)
            prob_unet = torch.sigmoid(out_unet).squeeze().cpu().numpy()
        latencies_unet.append((time.perf_counter() - t0) * 1000.0)

        clean_unet = postprocess_prediction(prob_unet, threshold=0.50)
        m_unet = compute_segmentation_metrics(clean_unet, gt_np)
        metrics_unet_list.append(m_unet)

        # 2. Inference Attention U-Net
        t0 = time.perf_counter()
        with torch.no_grad():
            out_att = model_att(img_t)
            prob_att = torch.sigmoid(out_att).squeeze().cpu().numpy()
        latencies_att.append((time.perf_counter() - t0) * 1000.0)

        clean_att = postprocess_prediction(prob_att, threshold=0.50)
        m_att = compute_segmentation_metrics(clean_att, gt_np)
        metrics_att_list.append(m_att)

        # Render 5-panel qualitative comparison on selected sample cases
        if idx in [10, 50, 100, 150, 200]:
            case_name = meta["file_name"][0]
            raw_img_np = (img_t.squeeze().cpu().numpy() * 255.0).astype(np.uint8)

            # Extract centerline and estimate diameter on Attention U-Net prediction
            skel = extract_centerline(clean_att)
            d_res = estimate_vessel_diameters(clean_att, skel)

            fig_path = PLOTS_DIR / f"test_case_{idx}_{Path(case_name).stem}.png"
            render_5panel_comparison(
                raw_img=raw_img_np,
                gt_mask=gt_np,
                unet_mask=clean_unet,
                att_unet_mask=clean_att,
                skeleton=skel,
                diameter_map=d_res["diameter_map"],
                metrics_unet=m_unet,
                metrics_att=m_att,
                case_name=case_name,
                save_path=fig_path,
            )

    # Compute mean statistics
    def summarize(metric_list, lat_list):
        return {
            "dice_mean": float(np.mean([m["dice"] for m in metric_list])),
            "dice_std": float(np.std([m["dice"] for m in metric_list])),
            "iou_mean": float(np.mean([m["iou"] for m in metric_list])),
            "iou_std": float(np.std([m["iou"] for m in metric_list])),
            "precision_mean": float(np.mean([m["precision"] for m in metric_list])),
            "recall_mean": float(np.mean([m["recall"] for m in metric_list])),
            "specificity_mean": float(np.mean([m["specificity"] for m in metric_list])),
            "latency_mean_ms": float(np.mean(lat_list)),
            "fps": float(1000.0 / np.mean(lat_list)),
        }

    sum_unet = summarize(metrics_unet_list, latencies_unet)
    sum_att = summarize(metrics_att_list, latencies_att)

    results = {
        "dataset": "ARCADE SYNTAX Test Split",
        "num_test_images": len(test_loader),
        "models": {
            "UNet": sum_unet,
            "AttentionUNet": sum_att,
        },
        "superior_model": "AttentionUNet" if sum_att["dice_mean"] >= sum_unet["dice_mean"] else "UNet",
    }

    # Save results JSON
    res_path = EVAL_DIR / "comparison_results.json"
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Print comparative results table
    print("\n" + "=" * 85)
    print(f"{'Metric':<25} | {'Baseline U-Net':<25} | {'Attention U-Net':<25}")
    print("-" * 85)
    print(f"{'Dice Similarity Coeff':<25} | {sum_unet['dice_mean']:.4f} +/- {sum_unet['dice_std']:.4f}        | {sum_att['dice_mean']:.4f} +/- {sum_att['dice_std']:.4f} {'[BEST]' if sum_att['dice_mean'] >= sum_unet['dice_mean'] else ''}")
    print(f"{'Intersection over Union':<25} | {sum_unet['iou_mean']:.4f} +/- {sum_unet['iou_std']:.4f}        | {sum_att['iou_mean']:.4f} +/- {sum_att['iou_std']:.4f}")
    print(f"{'Precision (PPV)':<25} | {sum_unet['precision_mean']:.4f}                    | {sum_att['precision_mean']:.4f}")
    print(f"{'Recall (Sensitivity)':<25} | {sum_unet['recall_mean']:.4f}                    | {sum_att['recall_mean']:.4f}")
    print(f"{'Specificity (TNR)':<25} | {sum_unet['specificity_mean']:.4f}                    | {sum_att['specificity_mean']:.4f}")
    print(f"{'Inference Latency':<25} | {sum_unet['latency_mean_ms']:.2f} ms ({sum_unet['fps']:.1f} FPS)         | {sum_att['latency_mean_ms']:.2f} ms ({sum_att['fps']:.1f} FPS)")
    print("=" * 85)
    print(f"Selected Best-Performing Model: {results['superior_model']}")
    print(f"Comparative report JSON saved at: {res_path}")
    print(f"Qualitative clinical panels saved in: {PLOTS_DIR}")

    return results


if __name__ == "__main__":
    run_evaluation()
