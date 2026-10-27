
import json
from pathlib import Path

import numpy as np
import torch
import matplotlib.pyplot as plt
from PIL import Image

from unet_model import UNet
from attention_unet import AttentionUNet


# 1. Define file paths
BASE_DIR = Path(__file__).resolve().parent

MANIFEST_PATH = (
    BASE_DIR / "outputs" / "artery_masks" / "val_manifest.json"
)

UNET_PATH = BASE_DIR / "outputs" / "unet" / "best_unet.pth"

ATTENTION_PATH = (
    BASE_DIR / "outputs" / "attention_unet" / "best_attention_unet.pth"
)

OUTPUT_DIR = BASE_DIR / "outputs" / "model_comparison"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

device = torch.device("cpu")


# 2. Check required files
for path in [MANIFEST_PATH, UNET_PATH, ATTENTION_PATH]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")


# 3. Load validation dataset manifest
with open(MANIFEST_PATH, "r", encoding="utf-8") as file:
    samples = json.load(file)

if not samples:
    raise ValueError("The validation manifest contains no samples.")

# Start with the first validation image
sample = samples[0]

image_path = Path(sample["image"])
mask_path = Path(sample["mask"])

image = np.array(
    Image.open(image_path).convert("L"),
    dtype=np.float32
) / 255.0

ground_truth = (
    np.array(Image.open(mask_path).convert("L")) >= 128
)


# 4. Prepare image for the models
image_tensor = torch.from_numpy(image).unsqueeze(0).unsqueeze(0)
image_tensor = image_tensor.to(device)


# 5. Load trained model checkpoints
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


# 6. Generate artery predictions
with torch.no_grad():
    unet_output = torch.sigmoid(unet(image_tensor))
    attention_output = torch.sigmoid(attention_unet(image_tensor))

unet_prediction = unet_output[0, 0].cpu().numpy() >= 0.5
attention_prediction = attention_output[0, 0].cpu().numpy() >= 0.5


# 7. Calculate Dice score and IoU for this image
def calculate_metrics(prediction, target):
    intersection = np.logical_and(prediction, target).sum()
    union = np.logical_or(prediction, target).sum()

    dice = (
        2.0 * intersection
        / (prediction.sum() + target.sum() + 1e-7)
    )

    iou = intersection / (union + 1e-7)

    return dice, iou


unet_dice, unet_iou = calculate_metrics(
    unet_prediction, ground_truth
)

attention_dice, attention_iou = calculate_metrics(
    attention_prediction, ground_truth
)


# 8. Display comparison results
print("\n========== MODEL COMPARISON ==========")
print(f"Validation image: {image_path.name}")

print("\nU-Net:")
print(f"Dice Score: {unet_dice:.4f}")
print(f"IoU Score:  {unet_iou:.4f}")

print("\nAttention U-Net:")
print(f"Dice Score: {attention_dice:.4f}")
print(f"IoU Score:  {attention_iou:.4f}")


# 9. Plot original image, true mask, and predictions
fig, axes = plt.subplots(2, 3, figsize=(15, 9))

axes[0, 0].imshow(image, cmap="gray")
axes[0, 0].set_title("Original Angiography Image")

axes[0, 1].imshow(ground_truth, cmap="gray")
axes[0, 1].set_title("Ground Truth Mask")

axes[0, 2].imshow(unet_prediction, cmap="gray")
axes[0, 2].set_title(f"U-Net Prediction (Dice: {unet_dice:.3f})")

axes[1, 0].imshow(image, cmap="gray")
axes[1, 0].imshow(unet_prediction, cmap="autumn", alpha=0.45)
axes[1, 0].set_title("U-Net Overlay")

axes[1, 1].imshow(attention_prediction, cmap="gray")
axes[1, 1].set_title(
    f"Attention U-Net Prediction (Dice: {attention_dice:.3f})"
)

axes[1, 2].imshow(image, cmap="gray")
axes[1, 2].imshow(
    attention_prediction, cmap="autumn", alpha=0.45
)
axes[1, 2].set_title("Attention U-Net Overlay")

for ax in axes.flat:
    ax.axis("off")

plt.tight_layout()

output_path = OUTPUT_DIR / "validation_prediction_comparison.png"
plt.savefig(output_path, dpi=200, bbox_inches="tight")

print(f"\nComparison image saved to:\n{output_path}")

plt.show()
