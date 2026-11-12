
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

VISUALIZATION_DIR = (
    OUTPUT_DIR / "dicebce_diagnostics"
)

CHECKPOINT_PATH = (
    OUTPUT_DIR / "best_stenosis_unet_dicebce.pth"
)

BASE_CHANNELS = 16
NUM_VISUALIZATIONS = 10
RANDOM_SEED = 42

THRESHOLDS = [0.01, 0.05, 0.10, 0.20, 0.50]


# --------------------------------------------------
# DEVICE
# --------------------------------------------------

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("=" * 60)
print("STENOSIS U-NET - BCE + DICE DIAGNOSTICS")
print("=" * 60)

print("Device:", DEVICE)
print("Checkpoint:", CHECKPOINT_PATH)


# --------------------------------------------------
# METRICS
# --------------------------------------------------

def calculate_metrics(prediction, ground_truth):

    prediction = prediction.astype(bool)
    ground_truth = ground_truth.astype(bool)

    intersection = np.logical_and(
        prediction, ground_truth
    ).sum()

    union = np.logical_or(
        prediction, ground_truth
    ).sum()

    dice = (
        2.0 * intersection /
        (prediction.sum() + ground_truth.sum() + 1e-8)
    )

    iou = intersection / (union + 1e-8)

    return float(dice), float(iou)


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

print("\nLoading checkpoint...")

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

print("Checkpoint loaded successfully.")
print("Best checkpoint epoch:", checkpoint.get("epoch"))
print("Checkpoint validation Dice:", checkpoint.get("val_dice"))


# --------------------------------------------------
# LOAD VALIDATION DATASET
# --------------------------------------------------

print("\nLoading validation dataset...")

dataset = StenosisDataset(split="val")

print("Validation samples:", len(dataset))

if len(dataset) == 0:
    raise RuntimeError("Validation dataset is empty.")


# --------------------------------------------------
# SELECT IMAGES FOR VISUALIZATION
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
# INITIALIZE RESULTS
# --------------------------------------------------

results = {
    threshold: {
        "dice": [],
        "iou": []
    }
    for threshold in THRESHOLDS
}

all_probabilities = []
all_predicted_pixels = []
all_ground_truth_pixels = []

csv_rows = []


# --------------------------------------------------
# EVALUATION
# --------------------------------------------------

print("\nEvaluating all validation images...\n")

for index in tqdm(
    range(len(dataset)),
    desc="Validation evaluation"
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

    # ----------------------------------------------
    # PROBABILITY DIAGNOSTICS
    # ----------------------------------------------

    mean_probability = float(
        probabilities.mean()
    )

    max_probability = float(
        probabilities.max()
    )

    min_probability = float(
        probabilities.min()
    )

    predicted_fraction_050 = float(
        (probabilities >= 0.50).mean()
    )

    predicted_fraction_010 = float(
        (probabilities >= 0.10).mean()
    )

    ground_truth_fraction = float(
        ground_truth.mean()
    )

    all_probabilities.append(mean_probability)

    all_predicted_pixels.append(
        predicted_fraction_050
    )

    all_ground_truth_pixels.append(
        ground_truth_fraction
    )

    row = {
        "image_index": index,
        "mean_probability": mean_probability,
        "max_probability": max_probability,
        "min_probability": min_probability,
        "predicted_percent_at_0.50":
            predicted_fraction_050 * 100,
        "predicted_percent_at_0.10":
            predicted_fraction_010 * 100,
        "ground_truth_percent":
            ground_truth_fraction * 100
    }

    # ----------------------------------------------
    # METRICS FOR EACH THRESHOLD
    # ----------------------------------------------

    for threshold in THRESHOLDS:

        prediction = probabilities >= threshold

        dice, iou = calculate_metrics(
            prediction,
            ground_truth
        )

        results[threshold]["dice"].append(dice)
        results[threshold]["iou"].append(iou)

        row[f"dice_{threshold}"] = dice
        row[f"iou_{threshold}"] = iou

    csv_rows.append(row)

    # ----------------------------------------------
    # SAVE SELECTED VISUALIZATIONS
    # ----------------------------------------------

    if index in selected_indices:

        fig, axes = plt.subplots(
            3,
            3,
            figsize=(15, 13)
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

        # Threshold predictions
        for position, threshold in enumerate(
            THRESHOLDS,
            start=3
        ):

            prediction = probabilities >= threshold

            dice, iou = calculate_metrics(
                prediction,
                ground_truth
            )

            axes[position].imshow(
                prediction,
                cmap="gray"
            )

            axes[position].set_title(
                f"Threshold {threshold:.2f}\n"
                f"Dice: {dice:.3f}, IoU: {iou:.3f}"
            )

        # Prediction overlay at threshold 0.10
        axes[8].imshow(
            original_image,
            cmap="gray"
        )

        prediction_010 = probabilities >= 0.10

        overlay = np.ma.masked_where(
            ~prediction_010,
            prediction_010
        )

        axes[8].imshow(
            overlay,
            cmap=ListedColormap(["red"]),
            alpha=0.55,
            vmin=0,
            vmax=1
        )

        axes[8].set_title(
            "Prediction Overlay (Threshold 0.10)"
        )

        for axis in axes:
            axis.axis("off")

        plt.tight_layout()

        plt.savefig(
            VISUALIZATION_DIR / f"image_{index}.png",
            dpi=150,
            bbox_inches="tight"
        )

        plt.close(fig)


# --------------------------------------------------
# SAVE PER-IMAGE METRICS
# --------------------------------------------------

csv_path = (
    VISUALIZATION_DIR /
    "dicebce_diagnostic_metrics.csv"
)

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
# PRINT PROBABILITY DIAGNOSTICS
# --------------------------------------------------

print("\n" + "=" * 60)
print("PROBABILITY DIAGNOSTICS")
print("=" * 60)

print(
    "Mean predicted probability:",
    f"{np.mean(all_probabilities):.6f}"
)

print(
    "Mean predicted stenosis pixels at threshold 0.50:",
    f"{np.mean(all_predicted_pixels) * 100:.6f}%"
)

print(
    "Mean ground-truth stenosis pixels:",
    f"{np.mean(all_ground_truth_pixels) * 100:.6f}%"
)

print(
    "Maximum probability across validation set:",
    f"{max(row['max_probability'] for row in csv_rows):.6f}"
)


# --------------------------------------------------
# PRINT THRESHOLD COMPARISON
# --------------------------------------------------

print("\n" + "=" * 60)
print("THRESHOLD COMPARISON")
print("=" * 60)

for threshold in THRESHOLDS:

    mean_dice = np.mean(
        results[threshold]["dice"]
    )

    mean_iou = np.mean(
        results[threshold]["iou"]
    )

    print(f"\nThreshold: {threshold:.2f}")
    print(f"Mean Dice: {mean_dice:.4f}")
    print(f"Mean IoU:  {mean_iou:.4f}")


# --------------------------------------------------
# FINISH
# --------------------------------------------------

print("\n" + "=" * 60)
print("DIAGNOSTICS COMPLETED")
print("=" * 60)

print("CSV saved to:")
print(csv_path)

print("\nVisualizations saved to:")
print(VISUALIZATION_DIR)
