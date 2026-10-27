
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

from unet_model import UNet
from attention_unet import AttentionUNet


# Project paths
BASE_DIR = Path(__file__).resolve().parent

MANIFEST_PATH = BASE_DIR / "outputs" / "artery_masks" / "val_manifest.json"
UNET_PATH = BASE_DIR / "outputs" / "unet" / "best_unet.pth"
ATTENTION_PATH = (
    BASE_DIR / "outputs" / "attention_unet" / "best_attention_unet.pth"
)

device = torch.device("cpu")


# Load validation images and masks
with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
    samples = json.load(f)

print(f"Validation images: {len(samples)}")


# Load a trained model
def load_model(model, checkpoint_path):
    checkpoint = torch.load(
        checkpoint_path,
        map_location=device,
        weights_only=True
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model


unet = load_model(UNet(), UNET_PATH)
attention_unet = load_model(AttentionUNet(), ATTENTION_PATH)


# Calculate Dice and IoU for one image
def calculate_metrics(prediction, target):
    intersection = np.logical_and(prediction, target).sum()
    union = np.logical_or(prediction, target).sum()

    dice = (
        2.0 * intersection
        / (prediction.sum() + target.sum() + 1e-7)
    )
    iou = intersection / (union + 1e-7)

    return dice, iou


# Evaluate every validation image
results = {
    "U-Net": {"dice": [], "iou": []},
    "Attention U-Net": {"dice": [], "iou": []},
}

with torch.no_grad():
    for sample in tqdm(samples, desc="Evaluating models"):
        image = np.array(
            Image.open(sample["image"]).convert("L"),
            dtype=np.float32
        ) / 255.0

        target = (
            np.array(Image.open(sample["mask"]).convert("L")) >= 128
        )

        image_tensor = torch.from_numpy(image).unsqueeze(0).unsqueeze(0)
        image_tensor = image_tensor.to(device)

        # U-Net prediction
        unet_prediction = (
            torch.sigmoid(unet(image_tensor))[0, 0]
            .cpu().numpy() >= 0.5
        )

        # Attention U-Net prediction
        attention_prediction = (
            torch.sigmoid(attention_unet(image_tensor))[0, 0]
            .cpu().numpy() >= 0.5
        )

        # Calculate metrics for each image separately
        dice, iou = calculate_metrics(unet_prediction, target)
        results["U-Net"]["dice"].append(dice)
        results["U-Net"]["iou"].append(iou)

        dice, iou = calculate_metrics(attention_prediction, target)
        results["Attention U-Net"]["dice"].append(dice)
        results["Attention U-Net"]["iou"].append(iou)


# Display average results across the validation set
print("\n========== FULL VALIDATION RESULTS ==========")

for model_name, metrics in results.items():
    mean_dice = np.mean(metrics["dice"])
    mean_iou = np.mean(metrics["iou"])

    print(f"\n{model_name}")
    print(f"Mean Dice Score: {mean_dice:.4f} ({mean_dice * 100:.2f}%)")
    print(f"Mean IoU Score:  {mean_iou:.4f} ({mean_iou * 100:.2f}%)")

# Compare the models
dice_difference = (
    np.mean(results["Attention U-Net"]["dice"])
    - np.mean(results["U-Net"]["dice"])
)

print("\n========== COMPARISON ==========")
print(f"Attention U-Net minus U-Net Dice: {dice_difference:+.4f}")

if dice_difference > 0:
    print("Attention U-Net has the higher mean Dice score.")
elif dice_difference < 0:
    print("U-Net has the higher mean Dice score.")
else:
    print("Both models have the same mean Dice score.")
