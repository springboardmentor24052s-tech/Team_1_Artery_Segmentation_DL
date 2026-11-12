
import sys
import csv
import random
from pathlib import Path

import numpy as np
import torch
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from tqdm import tqdm


# --------------------------------------------------
# PROJECT PATHS AND IMPORTS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(PROJECT_ROOT))

from stenosis_unet import StenosisUNet
from stenosis_dataset import StenosisDataset


OUTPUT_DIR = MODEL_DIR / "outputs"

# NEW: Separate folder for extended model evaluation
RESULTS_DIR = OUTPUT_DIR / "extended_final_test_evaluation"

VISUALIZATION_DIR = RESULTS_DIR / "visualizations"

# NEW: Load extended BCE + Dice checkpoint
CHECKPOINT_PATH = (
    OUTPUT_DIR / "best_stenosis_unet_dicebce_extended.pth"
)

BASE_CHANNELS = 16

# Selected using validation data only
THRESHOLD = 0.05

NUM_VISUALIZATIONS = 10

RANDOM_SEED = 42


# --------------------------------------------------
# DEVICE
# --------------------------------------------------

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 70)
print("STENOSIS U-NET - EXTENDED MODEL FINAL TEST EVALUATION")
print("=" * 70)

print("Device:", DEVICE)
print("Checkpoint:", CHECKPOINT_PATH)
print("Threshold:", THRESHOLD)
print("Results folder:", RESULTS_DIR)


# --------------------------------------------------
# METRICS
# --------------------------------------------------

def calculate_metrics(prediction, ground_truth):

    prediction = prediction.astype(bool)
    ground_truth = ground_truth.astype(bool)

    intersection = np.logical_and(
        prediction,
        ground_truth
    ).sum()

    prediction_pixels = prediction.sum()
    ground_truth_pixels = ground_truth.sum()

    union = np.logical_or(
        prediction,
        ground_truth
    ).sum()

    dice = (
        2.0 * intersection /
        (prediction_pixels + ground_truth_pixels + 1e-8)
    )

    iou = intersection / (union + 1e-8)

    return (
        float(dice),
        float(iou),
        int(intersection),
        int(prediction_pixels),
        int(ground_truth_pixels)
    )


# --------------------------------------------------
# LOAD CHECKPOINT
# --------------------------------------------------

print("\nLoading extended BCE + Dice model...")

if not CHECKPOINT_PATH.exists():

    raise FileNotFoundError(
        f"Checkpoint not found: {CHECKPOINT_PATH}"
    )

checkpoint = torch.load(
    CHECKPOINT_PATH,
    map_location=DEVICE,
    weights_only=False
)

model = StenosisUNet(
    in_channels=1,
    out_channels=1,
    base_channels=BASE_CHANNELS
).to(DEVICE)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model.eval()

print("Model loaded successfully.")
print("Checkpoint epoch:", checkpoint.get("epoch"))
print("Checkpoint validation Dice:", checkpoint.get("val_dice"))


# --------------------------------------------------
# LOAD TEST DATASET
# --------------------------------------------------

print("\nLoading test dataset...")

dataset = StenosisDataset(split="test")

print("Test samples:", len(dataset))

if len(dataset) == 0:

    raise RuntimeError("Test dataset is empty.")

if len(dataset) != 300:

    print(
        "WARNING: Expected 300 test samples, "
        f"but found {len(dataset)}."
    )


# --------------------------------------------------
# SELECT VISUALIZATION IMAGES
# --------------------------------------------------

random.seed(RANDOM_SEED)

selected_indices = set(
    random.sample(
        range(len(dataset)),
        min(NUM_VISUALIZATIONS, len(dataset))
    )
)

VISUALIZATION_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# INITIALIZE METRICS
# --------------------------------------------------

image_dice_scores = []
image_iou_scores = []

total_intersection = 0
total_prediction_pixels = 0
total_ground_truth_pixels = 0

csv_rows = []


# --------------------------------------------------
# TEST EVALUATION
# --------------------------------------------------

print("\nStarting extended model final test evaluation...\n")

for index in tqdm(
    range(len(dataset)),
    desc="Extended model test evaluation"
):

    image, mask = dataset[index]

    input_tensor = image.unsqueeze(0).to(DEVICE)

    ground_truth = (
        mask.squeeze().cpu().numpy() > 0.5
    )

    with torch.no_grad():

        logits = model(input_tensor)

        probabilities = torch.sigmoid(logits)

    probabilities = (
        probabilities.squeeze().cpu().numpy()
    )

    prediction = probabilities >= THRESHOLD

    (
        dice,
        iou,
        intersection,
        prediction_pixels,
        ground_truth_pixels
    ) = calculate_metrics(
        prediction,
        ground_truth
    )

    image_dice_scores.append(dice)
    image_iou_scores.append(iou)

    total_intersection += intersection
    total_prediction_pixels += prediction_pixels
    total_ground_truth_pixels += ground_truth_pixels

    csv_rows.append({
        "image_index": index,
        "dice": dice,
        "iou": iou,
        "predicted_pixels": prediction_pixels,
        "ground_truth_pixels": ground_truth_pixels,
        "intersection_pixels": intersection,
        "mean_probability": float(probabilities.mean()),
        "max_probability": float(probabilities.max())
    })

    # ----------------------------------------------
    # SAVE SELECTED VISUALIZATIONS
    # ----------------------------------------------

    if index in selected_indices:

        fig, axes = plt.subplots(
            2,
            3,
            figsize=(15, 10)
        )

        axes = axes.flatten()

        original_image = image.squeeze().cpu().numpy()

        # Original image
        axes[0].imshow(
            original_image,
            cmap="gray"
        )

        axes[0].set_title("Original Image")

        # Ground truth
        axes[1].imshow(
            ground_truth,
            cmap="gray"
        )

        axes[1].set_title("Ground Truth")

        # Probability map
        axes[2].imshow(
            probabilities,
            cmap="viridis",
            vmin=0,
            vmax=1
        )

        axes[2].set_title("Probability Map")

        # Prediction
        axes[3].imshow(
            prediction,
            cmap="gray"
        )

        axes[3].set_title(
            f"Prediction (Threshold {THRESHOLD})"
        )

        # Overlay
        axes[4].imshow(
            original_image,
            cmap="gray"
        )

        overlay = np.ma.masked_where(
            ~prediction,
            prediction
        )

        axes[4].imshow(
            overlay,
            cmap=ListedColormap(["red"]),
            alpha=0.55,
            vmin=0,
            vmax=1
        )

        axes[4].set_title("Prediction Overlay")

        # Ground truth vs prediction
        comparison = np.zeros(
            (*ground_truth.shape, 3),
            dtype=np.float32
        )

        # Green: correctly predicted pixels
        true_positive = prediction & ground_truth

        # Red: false-positive pixels
        false_positive = prediction & ~ground_truth

        # Blue: false-negative pixels
        false_negative = ~prediction & ground_truth

        comparison[true_positive] = [0, 1, 0]
        comparison[false_positive] = [1, 0, 0]
        comparison[false_negative] = [0, 0, 1]

        axes[5].imshow(comparison)

        axes[5].set_title(
            f"Comparison\nDice: {dice:.3f}, IoU: {iou:.3f}"
        )

        for axis in axes:
            axis.axis("off")

        plt.tight_layout()

        plt.savefig(
            VISUALIZATION_DIR / f"test_image_{index}.png",
            dpi=150,
            bbox_inches="tight"
        )

        plt.close(fig)


# --------------------------------------------------
# CALCULATE FINAL METRICS
# --------------------------------------------------

mean_dice = float(np.mean(image_dice_scores))
mean_iou = float(np.mean(image_iou_scores))

global_dice = (
    2.0 * total_intersection /
    (
        total_prediction_pixels +
        total_ground_truth_pixels +
        1e-8
    )
)

global_iou = (
    total_intersection /
    (
        total_prediction_pixels +
        total_ground_truth_pixels -
        total_intersection +
        1e-8
    )
)


# --------------------------------------------------
# SAVE PER-IMAGE CSV
# --------------------------------------------------

csv_path = RESULTS_DIR / "extended_test_image_metrics.csv"

with open(
    csv_path,
    "w",
    newline=""
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=csv_rows[0].keys()
    )

    writer.writeheader()
    writer.writerows(csv_rows)


# --------------------------------------------------
# SAVE SUMMARY
# --------------------------------------------------

summary_path = (
    RESULTS_DIR / "extended_final_test_summary.txt"
)

with open(summary_path, "w") as file:

    file.write("STENOSIS U-NET - EXTENDED MODEL FINAL TEST RESULTS\n")
    file.write("=" * 60 + "\n")

    file.write(f"Test images: {len(dataset)}\n")
    file.write(f"Checkpoint epoch: {checkpoint.get('epoch')}\n")
    file.write(f"Checkpoint validation Dice: {checkpoint.get('val_dice')}\n")
    file.write(f"Threshold: {THRESHOLD}\n")
    file.write(f"Mean Dice: {mean_dice:.6f}\n")
    file.write(f"Mean IoU: {mean_iou:.6f}\n")
    file.write(f"Global Dice: {global_dice:.6f}\n")
    file.write(f"Global IoU: {global_iou:.6f}\n")


# --------------------------------------------------
# PRINT RESULTS
# --------------------------------------------------

print("\n" + "=" * 70)
print("EXTENDED STENOSIS U-NET - FINAL TEST RESULTS")
print("=" * 70)

print("Number of test images:", len(dataset))
print("Checkpoint epoch:", checkpoint.get("epoch"))
print("Checkpoint validation Dice:", checkpoint.get("val_dice"))
print("Evaluation threshold:", THRESHOLD)

print("\nMean Dice Score:", f"{mean_dice:.4f}")
print("Mean IoU Score: ", f"{mean_iou:.4f}")

print("\nGlobal Dice Score:", f"{global_dice:.4f}")
print("Global IoU Score: ", f"{global_iou:.4f}")

print("=" * 70)


# --------------------------------------------------
# FINISH
# --------------------------------------------------

print("\nExtended model final test evaluation completed successfully!")

print("\nResults saved in:")
print(RESULTS_DIR)

print("\nMetrics CSV:")
print(csv_path)

print("\nSummary:")
print(summary_path)

print("\nVisualizations:")
print(VISUALIZATION_DIR)

print("\nNo model training was performed.")
print("No checkpoint was modified.")
print("Previous evaluation results were not overwritten.")
