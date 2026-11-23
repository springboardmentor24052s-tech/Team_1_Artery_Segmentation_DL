"""Convert ARCADE COCO annotations into training masks + run exploratory data analysis.

ARCADE (Popov et al., 2023, CC0): X-ray coronary angiography, 512x512.
  syntax/   1000 train / 200 val / 300 test  - polygons of 25 SYNTAX coronary segments
  stenosis/ 1000 train / 200 val / 300 test  - polygons of stenotic regions (category 26)

Output: data/processed/{syntax,stenosis}/{split}/{images,masks}/<id>.png  and  data/processed/eda.json
Usage:  python -m training.prepare_arcade
"""
from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from app.config import DATA_DIR
from app.ml.segments import ARCADE_SEGMENTS

RAW = DATA_DIR / "raw" / "arcade" / "arcade"
OUT = DATA_DIR / "processed"
STENOSIS_CAT = 26


def polys(seg) -> list:
    out = []
    for p in seg:
        a = np.array(p, np.float32).reshape(-1, 2)
        if len(a) >= 3:
            out.append(np.round(a).astype(np.int32))
    return out


def convert(task: str, split: str) -> dict:
    src = RAW / task / split
    ann = json.loads((src / "annotations" / f"{split}.json").read_text())
    dst = OUT / task / split
    for sub in ("images", "masks"):
        (dst / sub).mkdir(parents=True, exist_ok=True)
    by_img = {}
    for a in ann["annotations"]:
        by_img.setdefault(a["image_id"], []).append(a)
    stats = {"images": 0, "objects": 0, "per_class": Counter(), "fg_frac": [], "objs_per_img": [], "areas": []}
    for im in ann["images"]:
        h, w = im["height"], im["width"]
        img = cv2.imread(str(src / "images" / im["file_name"]), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        if img.shape != (512, 512):
            img = cv2.resize(img, (512, 512), interpolation=cv2.INTER_AREA)
        mask = np.zeros((h, w), np.uint8)
        anns = by_img.get(im["id"], [])
        if task == "syntax":
            anns = [a for a in anns if 1 <= a["category_id"] <= 25]
            for a in sorted(anns, key=lambda a: -a["area"]):  # small segments drawn on top
                cv2.fillPoly(mask, polys(a["segmentation"]), int(a["category_id"]))
                stats["per_class"][a["category_id"]] += 1
        else:
            anns = [a for a in anns if a["category_id"] == STENOSIS_CAT]
            for a in anns:
                cv2.fillPoly(mask, polys(a["segmentation"]), 255)
                stats["areas"].append(a["area"])
        if mask.shape != (512, 512):
            mask = cv2.resize(mask, (512, 512), interpolation=cv2.INTER_NEAREST)
        name = f"{split}_{im['id']:04d}.png"
        cv2.imwrite(str(dst / "images" / name), img)
        cv2.imwrite(str(dst / "masks" / name), mask)
        stats["images"] += 1
        stats["objects"] += len(anns)
        stats["objs_per_img"].append(len(anns))
        stats["fg_frac"].append(float((mask > 0).mean()))
    return {
        "images": stats["images"], "objects": stats["objects"],
        "objects_per_image_mean": round(float(np.mean(stats["objs_per_img"])), 2),
        "foreground_fraction_mean": round(float(np.mean(stats["fg_frac"])), 4),
        "per_class_counts": {ARCADE_SEGMENTS[k - 1][0]: v for k, v in sorted(stats["per_class"].items())},
        "lesion_area_px": ({"mean": round(float(np.mean(stats["areas"])), 1), "median": float(np.median(stats["areas"])),
                            "min": float(np.min(stats["areas"])), "max": float(np.max(stats["areas"]))} if stats["areas"] else None),
    }


def main():
    if not RAW.exists():
        raise SystemExit(f"ARCADE not found at {RAW}. Download https://zenodo.org/records/10390295 (arcade.zip) "
                         f"and unzip into data/raw/arcade/")
    if OUT.exists():
        for t in ("syntax", "stenosis"):
            shutil.rmtree(OUT / t, ignore_errors=True)
    eda = {"dataset": "ARCADE (X-ray coronary angiography, 512x512, CC0)", "source": "https://zenodo.org/records/10390295"}
    for task in ("syntax", "stenosis"):
        eda[task] = {}
        for split in ("train", "val", "test"):
            eda[task][split] = convert(task, split)
            print(task, split, eda[task][split]["images"], "images,", eda[task][split]["objects"], "objects")
    # intensity statistics
    ims = sorted((OUT / "syntax" / "train" / "images").glob("*.png"))[:200]
    vals = np.stack([cv2.imread(str(p), 0) for p in ims]).astype(np.float32)
    eda["intensity"] = {"mean": round(float(vals.mean()), 2), "std": round(float(vals.std()), 2)}
    (OUT / "eda.json").write_text(json.dumps(eda, indent=2))
    print("EDA written to", OUT / "eda.json")


if __name__ == "__main__":
    main()
