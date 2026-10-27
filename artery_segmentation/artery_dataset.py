
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset


OUTPUT_ROOT = (
    Path(__file__).resolve().parent / "outputs" / "artery_masks"
)


class ArteryDataset(Dataset):
    def __init__(self, split="train"):
        if split not in ("train", "val", "test"):
            raise ValueError(
                "split must be 'train', 'val', or 'test'"
            )

        manifest_path = OUTPUT_ROOT / f"{split}_manifest.json"

        with open(manifest_path, "r", encoding="utf-8") as file:
            self.samples = json.load(file)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]

        # Load the angiogram and its corresponding mask.
        image = Image.open(sample["image"]).convert("L")
        mask = Image.open(sample["mask"]).convert("L")

        # Normalize pixel values to the range 0 to 1.
        image = np.array(image, dtype=np.float32) / 255.0
        mask = np.array(mask, dtype=np.float32) / 255.0

        # Convert arrays to PyTorch tensors.
        image = torch.from_numpy(image).unsqueeze(0)
        mask = torch.from_numpy(mask).unsqueeze(0)

        return image, mask
