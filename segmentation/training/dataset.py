"""
StenoVision - Artery Segmentation Dataset Loader
================================================
Loads angiogram images and corresponding binary artery masks from the rasterized
manifests, applying on-the-fly preprocessing (CLAHE, intensity scaling) and data augmentations.
"""

import json
import random
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset


class ArterySegmentationDataset(Dataset):
    def __init__(
        self,
        manifest_path: str | Path,
        target_size: Tuple[int, int] = (512, 512),
        augment: bool = False,
        use_clahe: bool = True,
    ):
        self.manifest_path = Path(manifest_path)
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self.samples = json.load(f)

        self.target_size = target_size
        self.augment = augment
        self.use_clahe = use_clahe
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)) if use_clahe else None

    def __len__(self) -> int:
        return len(self.samples)

    def _apply_augmentations(self, image: np.ndarray, mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        # Random horizontal flip
        if random.random() > 0.5:
            image = np.fliplr(image)
            mask = np.fliplr(mask)

        # Random vertical flip
        if random.random() > 0.5:
            image = np.flipud(image)
            mask = np.flipud(mask)

        # Random small rotation (+- 10 degrees)
        if random.random() > 0.5:
            angle = random.uniform(-10.0, 10.0)
            h, w = image.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            image = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            mask = cv2.warpAffine(mask, M, (w, h), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

        # Random brightness / contrast jitter on image only
        if random.random() > 0.5:
            alpha = random.uniform(0.85, 1.15)  # contrast
            beta = random.uniform(-15, 15)      # brightness
            image = np.clip(alpha * image + beta, 0, 255).astype(np.uint8)

        return image, mask

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor, dict]:
        sample = self.samples[index]
        img_path = sample["image_path"]
        mask_path = sample["mask_path"]

        # 1. Load image and mask as 8-bit grayscale
        img = np.array(Image.open(img_path).convert("L"))
        mask = np.array(Image.open(mask_path).convert("L"))

        # 2. Resize if necessary
        if img.shape != self.target_size:
            img = cv2.resize(img, self.target_size, interpolation=cv2.INTER_LINEAR)
            mask = cv2.resize(mask, self.target_size, interpolation=cv2.INTER_NEAREST)

        # 3. Apply CLAHE if enabled
        if self.use_clahe and self.clahe is not None:
            img = self.clahe.apply(img)

        # 4. Apply training augmentations
        if self.augment:
            img, mask = self._apply_augmentations(img, mask)

        # 5. Normalize image [0.0, 1.0] and binarize mask {0.0, 1.0}
        img_tensor = torch.from_numpy(img.astype(np.float32) / 255.0).unsqueeze(0)  # (1, 512, 512)
        mask_tensor = torch.from_numpy((mask > 127).astype(np.float32)).unsqueeze(0)  # (1, 512, 512)

        meta = {
            "image_id": sample.get("image_id"),
            "file_name": sample.get("file_name"),
            "raw_path": img_path,
        }

        return img_tensor, mask_tensor, meta

