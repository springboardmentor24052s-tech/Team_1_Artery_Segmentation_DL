
"""Compare U-Net and Attention U-Net for artery segmentation.

Required manifest format:
[
  {
    "image": "images/001.png",
    "mask": "masks/001.png",
    "stenosis_label": 1,
    "unet_stenosis_score": 0.82,
    "attention_unet_stenosis_score": 0.76
  }
]

Image and mask paths are relative to the manifest file unless absolute.
Stenosis fields are optional and require independently validated labels/scores.
"""

import argparse
import csv
import json
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image
from tqdm import tqdm
from scipy.ndimage import binary_erosion, distance_transform_edt

from unet_model import UNet
from attention_unet import AttentionUNet


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST = BASE_DIR / "outputs" / "artery_masks" / "val_manifest.json"
DEFAULT_UNET = BASE_DIR / "outputs" / "unet" / "best_unet.pth"
DEFAULT_ATTENTION = (
    BASE_DIR / "outputs" / "attention_unet" / "best_attention_unet.pth"
)
DEFAULT_OUTPUT = BASE_DIR / "outputs" / "model_comparison"
DEVICE = torch.device("cpu")
EPS = 1e-8


def resolve_path(value, base):
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def load_model(model, checkpoint_path):
    if not checkpoint_path.is_file():
        raise FileNotFoundError(
            f"Checkpoint not found: {checkpoint_path}"
        )

    checkpoint = torch.load(
        checkpoint_path, map_location=DEVICE, weights_only=True
    )
    state = (
        checkpoint.get("model_state_dict", checkpoint)
        if isinstance(checkpoint, dict)
        else checkpoint
    )
    model.load_state_dict(state)
    model.to(DEVICE)
    model.eval()
    return model


def read_gray(path):
    if not path.is_file():
        raise FileNotFoundError(f"Image or mask not found: {path}")
    return np.asarray(Image.open(path).convert("L"))


def predict(model, image, threshold):
    tensor = torch.from_numpy(
        image.astype(np.float32) / 255.0
    ).unsqueeze(0).unsqueeze(0)

    with torch.inference_mode():
        output = model(tensor.to(DEVICE))
        probability = torch.sigmoid(output)[0, 0].cpu().numpy()

    return probability >= threshold


def surface_metrics(pred, target):
    """Symmetric Hausdorff and average surface distance, in pixels."""
    pred = np.asarray(pred, dtype=bool)
    target = np.asarray(target, dtype=bool)

    if not pred.any() and not target.any():
        return 0.0, 0.0
    if not pred.any() or not target.any():
        return float("nan"), float("nan")

    structure = np.ones((3, 3), dtype=bool)
    pred_surface = pred & ~binary_erosion(
        pred, structure=structure, border_value=0
    )
    target_surface = target & ~binary_erosion(
        target, structure=structure, border_value=0
    )

    dist_to_target = distance_transform_edt(~target_surface)
    dist_to_pred = distance_transform_edt(~pred_surface)

    pred_to_target = dist_to_target[pred_surface]
    target_to_pred = dist_to_pred[target_surface]

    hausdorff = max(
        float(pred_to_target.max()),
        float(target_to_pred.max()),
    )

    average_surface = float(
        (pred_to_target.sum() + target_to_pred.sum())
        / (len(pred_to_target) + len(target_to_pred))
    )

    return hausdorff, average_surface


def segmentation_metrics(pred, target):
    """Calculate pixel classification and boundary metrics."""
    pred = np.asarray(pred, dtype=bool)
    target = np.asarray(target, dtype=bool)

    tp = int(np.sum(pred & target))
    fp = int(np.sum(pred & ~target))
    fn = int(np.sum(~pred & target))
    tn = int(np.sum(~pred & ~target))

    dice = 2 * tp / (2 * tp + fp + fn + EPS)
    iou = tp / (tp + fp + fn + EPS)
    accuracy = (tp + tn) / (tp + tn + fp + fn + EPS)
    precision = tp / (tp + fp + EPS)
    recall = tp / (tp + fn + EPS)
    specificity = tn / (tn + fp + EPS)

    hausdorff, average_surface = surface_metrics(pred, target)

    return {
        "dice": dice,
        "iou": iou,
        "pixel_accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "sensitivity": recall,
        "specificity": specificity,
        "hausdorff_distance_px": hausdorff,
        "average_surface_distance_px": average_surface,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def binary_auc(labels, scores):
    """ROC AUC calculated from positive-negative score comparisons."""
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)

    positive = scores[labels == 1]
    negative = scores[labels == 0]

    if len(positive) == 0 or len(negative) == 0:
        return float("nan")

    comparisons = positive[:, None] - negative[None, :]
    return float(
        ((comparisons > 0).sum() + 0.5 * (comparisons == 0).sum())
        / comparisons.size
    )


def stenosis_metrics(labels, scores, threshold=0.5):
    """Evaluate binary stenosis predictions from independent scores."""
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)

    if not np.isin(labels, [0, 1]).all():
        raise ValueError("Stenosis labels must be 0 or 1.")
    if not np.isfinite(scores).all() or (
        (scores < 0).any() or (scores > 1).any()
    ):
        raise ValueError("Stenosis scores must be finite values in [0, 1].")

    predicted = scores >= threshold

    tp = int(np.sum(predicted & (labels == 1)))
    fp = int(np.sum(predicted & (labels == 0)))
    fn = int(np.sum(~predicted & (labels == 1)))
    tn = int(np.sum(~predicted & (labels == 0)))

    precision = tp / (tp + fp + EPS)
    recall = tp / (tp + fn + EPS)

    return {
        "accuracy": (tp + tn) / (tp + tn + fp + fn + EPS),
        "precision": precision,
        "recall": recall,
        "f1_score": 2 * precision * recall / (precision + recall + EPS),
        "sensitivity": recall,
        "specificity": tn / (tn + fp + EPS),
        "auc_roc": binary_auc(labels, scores),
        "false_positive_rate": fp / (fp + tn + EPS),
        "false_negative_rate": fn / (fn + tp + EPS),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def save_visual(image, target, unet_pred, attention_pred, title, path):
    """Save a five-panel visual comparison."""
    fig, axes = plt.subplots(1, 5, figsize=(18, 4))

    panels = [
        (image, "Input image", "gray"),
        (target, "Ground truth", "gray"),
        (unet_pred, "U-Net prediction", "gray"),
        (attention_pred, "Attention U-Net", "gray"),
    ]

    for ax, (data, label, cmap) in zip(axes[:4], panels):
        ax.imshow(data, cmap=cmap, vmin=0, vmax=255 if label == "Input image" else 1)
        ax.set_title(label)
        ax.axis("off")

    agreement = np.zeros((*target.shape, 3), dtype=np.uint8)
    agreement[unet_pred & attention_pred] = (0, 190, 0)
    agreement[unet_pred & ~attention_pred] = (255, 70, 70)
    agreement[attention_pred & ~unet_pred] = (70, 100, 255)

    axes[4].imshow(agreement)
    axes[4].set_title("Agreement / difference\nGreen: both; red/blue: differ")
    axes[4].axis("off")

    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)



def compare_existing_predictions(output_dir, visualize=8):
    """Fallback when no ground-truth manifest exists.

    Compares already-generated U-Net and Attention U-Net masks. These are
    agreement metrics only; they are NOT segmentation accuracy metrics.
    """
    candidates = [
        (BASE_DIR / "outputs" / "postprocessing" / "unet_cleaned",
         BASE_DIR / "outputs" / "postprocessing" / "attention_unet_cleaned"),
        (BASE_DIR / "outputs" / "postprocessing" / "unet_raw",
         BASE_DIR / "outputs" / "postprocessing" / "attention_unet_raw"),
    ]
    supported = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
    pairs = None
    selected_dirs = None
    for unet_dir, attention_dir in candidates:
        if not unet_dir.is_dir() or not attention_dir.is_dir():
            continue
        unet_files = {f.name.lower(): f for f in unet_dir.iterdir()
                      if f.is_file() and f.suffix.lower() in supported}
        attention_files = {f.name.lower(): f for f in attention_dir.iterdir()
                           if f.is_file() and f.suffix.lower() in supported}
        common = sorted(set(unet_files) & set(attention_files))
        if common:
            pairs = [(unet_files[name], attention_files[name]) for name in common]
            selected_dirs = (unet_dir, attention_dir)
            break

    if not pairs:
        raise FileNotFoundError(
            "No validation manifest was found and no matching saved prediction masks "
            "were found. Expected paired masks in outputs/postprocessing/" 
            "unet_cleaned and attention_unet_cleaned (or the corresponding *_raw folders). "
            "For accuracy metrics, provide a manifest containing original images and "
            "independent ground-truth masks."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    visual_dir = output_dir / "visualizations"
    visual_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, (unet_path, attention_path) in enumerate(pairs):
        a = read_gray(unet_path) >= 128
        b_img = Image.open(attention_path).convert("L")
        if b_img.size != (a.shape[1], a.shape[0]):
            b_img = b_img.resize((a.shape[1], a.shape[0]), Image.Resampling.NEAREST)
        b = np.asarray(b_img) >= 128

        tp = int(np.logical_and(a, b).sum())
        fp = int(np.logical_and(a, ~b).sum())
        fn = int(np.logical_and(~a, b).sum())
        union = int(np.logical_or(a, b).sum())
        dice = (2.0 * tp / (int(a.sum()) + int(b.sum()))) if (a.sum() + b.sum()) else 1.0
        iou = (tp / union) if union else 1.0
        rows.append({
            "filename": unet_path.name,
            "agreement_dice": dice,
            "agreement_iou": iou,
            "unet_vessel_pixels": int(a.sum()),
            "attention_unet_vessel_pixels": int(b.sum()),
            "different_pixels": int(np.logical_xor(a, b).sum()),
            "comparison_type": "prediction agreement only; no ground truth",
        })

        if index < max(0, visualize):
            agreement = np.zeros((*a.shape, 3), dtype=np.uint8)
            agreement[a & b] = (0, 190, 0)       # both models predict vessel
            agreement[a & ~b] = (255, 70, 70)    # U-Net only
            agreement[~a & b] = (70, 100, 255)   # Attention U-Net only
            fig, axes = plt.subplots(1, 3, figsize=(12, 4))
            axes[0].imshow(a, cmap="gray")
            axes[0].set_title("U-Net prediction")
            axes[1].imshow(b, cmap="gray")
            axes[1].set_title("Attention U-Net prediction")
            axes[2].imshow(agreement)
            axes[2].set_title("Agreement / difference\
Green: both; red/blue: differ")
            for ax in axes:
                ax.axis("off")
            fig.suptitle(f"{unet_path.name} — prediction agreement only")
            fig.tight_layout()
            fig.savefig(visual_dir / f"{index + 1:04d}_{unet_path.stem}.png",
                        dpi=150, bbox_inches="tight")
            plt.close(fig)

    csv_path = output_dir / "prediction_agreement.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "evaluation_type": "prediction agreement only; no ground truth",
        "number_of_paired_masks": len(rows),
        "source_directories": [str(selected_dirs[0]), str(selected_dirs[1])],
        "mean_agreement_dice": float(np.mean([r["agreement_dice"] for r in rows])),
        "mean_agreement_iou": float(np.mean([r["agreement_iou"] for r in rows])),
        "warning": (
            "Agreement between models is not a measure of segmentation accuracy. "
            "Dice, IoU, precision, recall, specificity, and surface distances against "
            "ground truth require independently labeled reference masks."
        ),
    }
    (output_dir / "prediction_agreement_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("\
No validation manifest found; ran prediction-agreement fallback.")
    print(f"Paired masks: {len(rows)}")
    print(f"Mean agreement Dice: {summary['mean_agreement_dice']:.4f}")
    print(f"Mean agreement IoU: {summary['mean_agreement_iou']:.4f}")
    print("These are model-agreement scores, not accuracy scores.")
    print(f"Reports saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate U-Net and Attention U-Net."
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--unet-checkpoint", default=str(DEFAULT_UNET))
    parser.add_argument(
        "--attention-checkpoint", default=str(DEFAULT_ATTENTION)
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--stenosis-threshold", type=float, default=0.5)
    parser.add_argument("--visualize", type=int, default=8)
    args = parser.parse_args()

    if not 0 < args.threshold < 1:
        parser.error("--threshold must be between 0 and 1.")
    if not 0 <= args.stenosis_threshold <= 1:
        parser.error("--stenosis-threshold must be between 0 and 1.")

    manifest_path = resolve_path(args.manifest, BASE_DIR)
    output_dir = resolve_path(args.output_dir, BASE_DIR)

    if not manifest_path.is_file():
        compare_existing_predictions(output_dir, visualize=args.visualize)
        return

    samples = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(samples, list) or not samples:
        raise ValueError("Manifest must be a non-empty JSON list.")

    unet = load_model(UNet(), resolve_path(args.unet_checkpoint, BASE_DIR))
    attention = load_model(
        AttentionUNet(),
        resolve_path(args.attention_checkpoint, BASE_DIR),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    visual_dir = output_dir / "visualizations"
    records = {"U-Net": [], "Attention U-Net": []}
    inference_times = {"U-Net": [], "Attention U-Net": []}
    per_image_rows = []

    stenosis_labels = []
    stenosis_scores = {"U-Net": [], "Attention U-Net": []}
    stenosis_complete = True

    for index, item in enumerate(tqdm(samples, desc="Evaluating models")):
        if not isinstance(item, dict) or not all(
            key in item for key in ("image", "mask")
        ):
            raise ValueError(
                f"Manifest item {index} must contain image and mask paths."
            )

        image_path = resolve_path(item["image"], manifest_path.parent)
        mask_path = resolve_path(item["mask"], manifest_path.parent)

        image = read_gray(image_path)
        raw_mask = read_gray(mask_path)

        if image.shape != raw_mask.shape:
            raise ValueError(
                f"Image/mask size mismatch: {image_path.name}"
            )

        # Ground-truth mask: white pixels are vessel pixels.
        target = raw_mask >= 128

        start = time.perf_counter()
        unet_pred = predict(unet, image, args.threshold)
        inference_times["U-Net"].append(time.perf_counter() - start)

        start = time.perf_counter()
        attention_pred = predict(attention, image, args.threshold)
        inference_times["Attention U-Net"].append(
            time.perf_counter() - start
        )

        unet_metrics = segmentation_metrics(unet_pred, target)
        attention_metrics = segmentation_metrics(attention_pred, target)

        records["U-Net"].append(unet_metrics)
        records["Attention U-Net"].append(attention_metrics)

        row = {"image": image_path.name}
        for prefix, metrics in (
            ("unet", unet_metrics),
            ("attention_unet", attention_metrics),
        ):
            row.update({f"{prefix}_{key}": value for key, value in metrics.items()})
        per_image_rows.append(row)

        required_stenosis = (
            "stenosis_label",
            "unet_stenosis_score",
            "attention_unet_stenosis_score",
        )
        if all(key in item for key in required_stenosis):
            stenosis_labels.append(int(item["stenosis_label"]))
            stenosis_scores["U-Net"].append(
                float(item["unet_stenosis_score"])
            )
            stenosis_scores["Attention U-Net"].append(
                float(item["attention_unet_stenosis_score"])
            )
        else:
            stenosis_complete = False

        if index < args.visualize:
            visual_dir.mkdir(parents=True, exist_ok=True)
            save_visual(
                image,
                target,
                unet_pred,
                attention_pred,
                image_path.name,
                visual_dir / f"{index + 1:04d}_{image_path.stem}.png",
            )

    csv_path = output_dir / "per_image_metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(per_image_rows[0]))
        writer.writeheader()
        writer.writerows(per_image_rows)

    metric_names = [
        "dice",
        "iou",
        "pixel_accuracy",
        "precision",
        "recall",
        "sensitivity",
        "specificity",
        "hausdorff_distance_px",
        "average_surface_distance_px",
    ]

    summary = {}
    for model_name, metric_rows in records.items():
        summary[model_name] = {
            metric: float(
                np.nanmean([row[metric] for row in metric_rows])
            )
            for metric in metric_names
        }
        summary[model_name]["mean_inference_seconds"] = float(
            np.mean(inference_times[model_name])
        )

    report = {
        "threshold": args.threshold,
        "number_of_images": len(samples),
        "distance_units": "pixels",
        "segmentation_metrics": summary,
    }

    if stenosis_complete and len(stenosis_labels) == len(samples):
        report["stenosis_evaluation"] = {
            model_name: stenosis_metrics(
                stenosis_labels, scores, args.stenosis_threshold
            )
            for model_name, scores in stenosis_scores.items()
        }
    else:
        report["stenosis_evaluation"] = {
            "status": "not_run",
            "reason": (
                "Every manifest entry must contain stenosis_label, "
                "unet_stenosis_score and attention_unet_stenosis_score."
            ),
        }

    (output_dir / "summary_metrics.json").write_text(
        json.dumps(report, indent=2, allow_nan=True),
        encoding="utf-8",
    )

    # Compare overlap/classification metrics.
    plot_metrics = [
        "dice", "iou", "pixel_accuracy", "precision",
        "sensitivity", "specificity",
    ]
    labels = [
        "Dice", "IoU", "Pixel accuracy", "Precision",
        "Sensitivity", "Specificity",
    ]
    x = np.arange(len(plot_metrics))
    width = 0.36

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(
        x - width / 2,
        [summary["U-Net"][metric] for metric in plot_metrics],
        width,
        label="U-Net",
    )
    ax.bar(
        x + width / 2,
        [summary["Attention U-Net"][metric] for metric in plot_metrics],
        width,
        label="Attention U-Net",
    )
    ax.set_ylabel("Mean score")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x, labels)
    ax.set_title(f"Segmentation metrics ({len(samples)} images)")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "metric_comparison.png", dpi=180)
    plt.close(fig)

    # Boundary distances have a different scale from overlap metrics.
    distance_metrics = [
        "hausdorff_distance_px",
        "average_surface_distance_px",
    ]
    distance_labels = ["Hausdorff distance (px)", "Average surface distance (px)"]
    x = np.arange(len(distance_metrics))

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(
        x - width / 2,
        [summary["U-Net"][metric] for metric in distance_metrics],
        width,
        label="U-Net",
    )
    ax.bar(
        x + width / 2,
        [summary["Attention U-Net"][metric] for metric in distance_metrics],
        width,
        label="Attention U-Net",
    )
    ax.set_xticks(x, distance_labels)
    ax.set_ylabel("Distance in pixels (lower is better)")
    ax.set_title("Boundary distance comparison")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "surface_distance_comparison.png", dpi=180)
    plt.close(fig)

    print("\nSEGMENTATION EVALUATION")
    for model_name in ("U-Net", "Attention U-Net"):
        print(f"\n{model_name}")
        for metric in metric_names:
            print(f"  {metric}: {summary[model_name][metric]:.4f}")
        print(
            "  mean_inference_seconds: "
            f"{summary[model_name]['mean_inference_seconds']:.4f}"
        )

    if report["stenosis_evaluation"].get("status") == "not_run":
        print("\nStenosis evaluation skipped:")
        print(report["stenosis_evaluation"]["reason"])

    print(f"\nReports saved to: {output_dir}")


if __name__ == "__main__":
    main()
