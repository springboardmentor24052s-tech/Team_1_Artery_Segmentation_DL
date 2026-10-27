
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

MANIFEST_PATH = (
    BASE_DIR / "outputs" / "artery_masks" / "val_manifest.json"
)

UNET_CHECKPOINT = (
    BASE_DIR / "outputs" / "unet" / "best_unet.pth"
)

ATTENTION_CHECKPOINT = (
    BASE_DIR / "outputs" / "attention_unet" / "best_attention_unet.pth"
)

OUTPUT_DIR = BASE_DIR / "outputs" / "postprocessing"

UNET_OUTPUT = OUTPUT_DIR / "unet_raw"
ATTENTION_OUTPUT = OUTPUT_DIR / "attention_unet_raw"

UNET_OUTPUT.mkdir(parents=True, exist_ok=True)
ATTENTION_OUTPUT.mkdir(parents=True, exist_ok=True)

device = torch.device("cpu")


# Load validation manifest
with open(MANIFEST_PATH, "r", encoding="utf-8") as file:
    samples = json.load(file)

print(f"Validation images found: {len(samples)}")


# Load model checkpoint
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


unet = load_model(UNet(), UNET_CHECKPOINT)
attention_unet = load_model(AttentionUNet(), ATTENTION_CHECKPOINT)


# Generate and save predictions
with torch.no_grad():
    for sample in tqdm(samples, desc="Generating predictions"):

        image_path = Path(sample["image"])

        image = np.array(
            Image.open(image_path).convert("L"),
            dtype=np.float32
        ) / 255.0

        image_tensor = torch.from_numpy(image).unsqueeze(0).unsqueeze(0)
        image_tensor = image_tensor.to(device)

        # U-Net prediction
        unet_probability = torch.sigmoid(unet(image_tensor))[0, 0]
        unet_mask = (
            unet_probability.cpu().numpy() >= 0.5
        ).astype(np.uint8) * 255

        # Attention U-Net prediction
        attention_probability = torch.sigmoid(
            attention_unet(image_tensor)
        )[0, 0]

        attention_mask = (
            attention_probability.cpu().numpy() >= 0.5
        ).astype(np.uint8) * 255

        # Save using the original image filename
        Image.fromarray(unet_mask).save(
            UNET_OUTPUT / image_path.name
        )

        Image.fromarray(attention_mask).save(
            ATTENTION_OUTPUT / image_path.name
        )


print("\nPrediction generation completed!")
print(f"U-Net masks: {UNET_OUTPUT}")
print(f"Attention U-Net masks: {ATTENTION_OUTPUT}")
print(f"Total masks generated per model: {len(samples)}")
