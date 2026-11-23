"""
StenoVision - COCO Detection Dataset Loader for Coronary Stenosis
=================================================================
Loads ARCADE Task 1 coronary artery stenosis bounding boxes and images
in standard torchvision detection format.
"""

import json
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset


class CoronaryStenosisDataset(Dataset):
    """
    PyTorch Dataset for coronary artery stenosis detection (Faster R-CNN).
    Reads ARCADE COCO-format JSON annotations and returns (image_tensor, target_dict).
    """

    def __init__(
        self,
        data_root: Union[str, Path],
        split: str = "train",
        transforms: Optional[Callable] = None,
        img_size: int = 512,
    ):
        super().__init__()
        self.data_root = Path(data_root)
        self.split = split
        self.transforms = transforms
        self.img_size = img_size

        self.images_dir = self.data_root / "data" / "stenosis" / split / "images"
        self.annotation_file = self.data_root / "data" / "stenosis" / split / "annotations" / f"{split}.json"

        if not self.annotation_file.exists():
            raise FileNotFoundError(f"Annotation file not found: {self.annotation_file}")

        with open(self.annotation_file, "r") as f:
            coco_data = json.load(f)

        self.images_info = {img["id"]: img for img in coco_data.get("images", [])}
        
        # Group annotations by image_id
        self.annotations_by_img: Dict[int, List[Dict]] = {img_id: [] for img_id in self.images_info}
        for ann in coco_data.get("annotations", []):
            img_id = ann["image_id"]
            if img_id in self.annotations_by_img:
                self.annotations_by_img[img_id].append(ann)

        self.image_ids = list(self.images_info.keys())
        print(f"[{split.upper()}] Loaded {len(self.image_ids)} images and {len(coco_data.get('annotations', []))} stenosis annotations.")

    def __len__(self) -> int:
        return len(self.image_ids)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        img_id = self.image_ids[idx]
        img_meta = self.images_info[img_id]
        img_path = self.images_dir / img_meta["file_name"]

        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            raise FileNotFoundError(f"Could not read image: {img_path}")

        orig_h, orig_w = img_bgr.shape[:2]

        # Resize if necessary
        if (orig_h, orig_w) != (self.img_size, self.img_size):
            img_resized = cv2.resize(img_bgr, (self.img_size, self.img_size), interpolation=cv2.INTER_LINEAR)
            sx = self.img_size / orig_w
            sy = self.img_size / orig_h
        else:
            img_resized = img_bgr
            sx, sy = 1.0, 1.0

        # Min-max / standard [0, 1] normalization
        img_float = img_resized.astype(np.float32) / 255.0
        # Convert BGR to RGB and [H, W, C] to [C, H, W]
        img_rgb = cv2.cvtColor(img_float, cv2.COLOR_BGR2RGB)
        img_tensor = torch.from_numpy(img_rgb).permute(2, 0, 1).float()

        raw_anns = self.annotations_by_img[img_id]
        boxes = []
        labels = []
        areas = []

        for ann in raw_anns:
            # COCO bbox: [x, y, width, height]
            x, y, w, h = ann["bbox"]
            x1 = max(0.0, float(x * sx))
            y1 = max(0.0, float(y * sy))
            x2 = min(float(self.img_size), float((x + w) * sx))
            y2 = min(float(self.img_size), float((y + h) * sy))

            # Filter degenerate / inverted boxes
            if (x2 - x1) >= 2.0 and (y2 - y1) >= 2.0:
                boxes.append([x1, y1, x2, y2])
                labels.append(1)  # Class 1 = Stenosis (Class 0 is background in torchvision)
                areas.append((x2 - x1) * (y2 - y1))

        if len(boxes) > 0:
            boxes_tensor = torch.as_tensor(boxes, dtype=torch.float32)
            labels_tensor = torch.as_tensor(labels, dtype=torch.int64)
            areas_tensor = torch.as_tensor(areas, dtype=torch.float32)
            iscrowd_tensor = torch.zeros((len(boxes),), dtype=torch.int64)
        else:
            boxes_tensor = torch.zeros((0, 4), dtype=torch.float32)
            labels_tensor = torch.zeros((0,), dtype=torch.int64)
            areas_tensor = torch.zeros((0,), dtype=torch.float32)
            iscrowd_tensor = torch.zeros((0,), dtype=torch.int64)

        target = {
            "boxes": boxes_tensor,
            "labels": labels_tensor,
            "image_id": torch.tensor([img_id]),
            "area": areas_tensor,
            "iscrowd": iscrowd_tensor,
            "orig_size": torch.as_tensor([orig_h, orig_w]),
            "file_name": img_meta["file_name"],
        }

        return img_tensor, target


def detection_collate_fn(batch):
    """Custom collate function for object detection batching."""
    return tuple(zip(*batch))

