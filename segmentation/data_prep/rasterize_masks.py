"""
StenoVision - Ground-Truth Mask Rasterization Pipeline
======================================================
Converts COCO JSON polygon segmentation annotations from the ARCADE SYNTAX benchmark
into standardized binary masks (512x512, uint8: 0=background, 255=coronary artery)
and generates sample manifests for PyTorch Dataset training.
"""

import json
import os
from pathlib import Path
import cv2
import numpy as np
from tqdm import tqdm


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SYNTAX_ROOT = PROJECT_ROOT / "data" / "syntax"
OUTPUT_MASKS_ROOT = PROJECT_ROOT / "data" / "masks"


def rasterize_split(split_name: str):
    ann_path = SYNTAX_ROOT / split_name / "annotations" / f"{split_name}.json"
    images_dir = SYNTAX_ROOT / split_name / "images"
    out_split_dir = OUTPUT_MASKS_ROOT / split_name
    out_split_dir.mkdir(parents=True, exist_ok=True)

    if not ann_path.exists():
        raise FileNotFoundError(f"Annotation file not found: {ann_path}")

    with open(ann_path, "r", encoding="utf-8") as f:
        coco_data = json.load(f)

    # Map image_id -> list of polygon annotations
    image_annotations = {}
    for ann in coco_data.get("annotations", []):
        img_id = ann["image_id"]
        if img_id not in image_annotations:
            image_annotations[img_id] = []
        image_annotations[img_id].append(ann)

    manifest_entries = []

    print(f"\nProcessing {split_name.upper()} split ({len(coco_data['images'])} images)...")
    for img_info in tqdm(coco_data["images"]):
        img_id = img_info["id"]
        file_name = img_info["file_name"]
        height = img_info.get("height", 512)
        width = img_info.get("width", 512)

        raw_image_path = images_dir / file_name
        mask_filename = Path(file_name).stem + "_mask.png"
        mask_save_path = out_split_dir / mask_filename

        # Create binary mask canvas
        mask = np.zeros((height, width), dtype=np.uint8)

        # Draw all polygon segments for this image
        anns = image_annotations.get(img_id, [])
        for ann in anns:
            seg = ann.get("segmentation", [])
            for poly in seg:
                if len(poly) >= 6:
                    pts = np.array(poly, dtype=np.int32).reshape(-1, 2)
                    cv2.fillPoly(mask, [pts], color=255)

        # Save binary mask
        cv2.imwrite(str(mask_save_path), mask)

        manifest_entries.append({
            "image_id": img_id,
            "image_path": str(raw_image_path.resolve()),
            "mask_path": str(mask_save_path.resolve()),
            "file_name": file_name,
            "width": width,
            "height": height,
            "num_annotations": len(anns),
            "vessel_pixel_ratio": float((mask > 0).sum() / (height * width))
        })

    # Save split manifest
    manifest_file = OUTPUT_MASKS_ROOT / f"{split_name}_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_entries, f, indent=2)

    print(f"Generated {len(manifest_entries)} masks and manifest at: {manifest_file}")
    return len(manifest_entries)


def main():
    OUTPUT_MASKS_ROOT.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("StenoVision: Rasterizing ARCADE SYNTAX Polygon Annotations to Masks")
    print("=" * 70)

    splits = ["train", "val", "test"]
    total = 0
    for split in splits:
        total += rasterize_split(split)

    print("\n" + "=" * 70)
    print(f"Mask rasterization completed! Total masks created: {total}")
    print(f"Output directory: {OUTPUT_MASKS_ROOT.resolve()}")
    print("=" * 70)


if __name__ == "__main__":
    main()

