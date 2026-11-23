"""
StenoVision - Exploratory Data Analysis (EDA) for ARCADE Dataset
================================================================
Parses the MICCAI ARCADE benchmark under datasets/1/data/, computes quantitative
statistics, evaluates plaque/vessel distributions, and generates visual charts.
"""

import sys
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set plotting style
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

# Prefer local dataset in StenoVision/data, fallback to datasets/1/data
local_data = PROJECT_ROOT / "StenoVision" / "data"
DATASET_ROOT = local_data if local_data.exists() else PROJECT_ROOT / "datasets" / "1" / "data"
OUTPUT_PLOTS_DIR = PROJECT_ROOT / "StenoVision" / "eda" / "plots"


def run_eda():
    OUTPUT_PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("StenoVision: ARCADE Dataset Exploratory Data Analysis (EDA)")
    print("=" * 70)

    if not DATASET_ROOT.exists():
        raise FileNotFoundError(f"Dataset root not found at {DATASET_ROOT.resolve()}")

    subsets = ["stenosis", "syntax"]
    splits = ["train", "val", "test"]

    summary = {
        "stenosis": {"images": {}, "annotations": {}, "categories": {}},
        "syntax": {"images": {}, "annotations": {}, "categories": {}},
    }
    
    stenosis_box_areas = []
    stenosis_aspect_ratios = []
    syntax_category_counts = {}
    syntax_category_names = {}

    for subset in subsets:
        for split in splits:
            ann_file = DATASET_ROOT / subset / split / "annotations" / f"{split}.json"
            if not ann_file.exists():
                print(f"Warning: Annotation file missing: {ann_file}")
                continue

            with open(ann_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            n_images = len(data.get("images", []))
            n_annotations = len(data.get("annotations", []))
            summary[subset]["images"][split] = n_images
            summary[subset]["annotations"][split] = n_annotations

            # Record categories
            for cat in data.get("categories", []):
                cat_id = cat["id"]
                cat_name = cat.get("name", f"Category {cat_id}")
                if subset == "syntax":
                    syntax_category_names[cat_id] = cat_name

            # Collect annotations stats
            for ann in data.get("annotations", []):
                if subset == "stenosis" and "bbox" in ann:
                    x, y, w, h = ann["bbox"]
                    if w > 0 and h > 0:
                        stenosis_box_areas.append(w * h)
                        stenosis_aspect_ratios.append(w / h)
                elif subset == "syntax":
                    cid = ann.get("category_id")
                    syntax_category_counts[cid] = syntax_category_counts.get(cid, 0) + 1

    print("\n--- Quantitative Partition Summary ---")
    for subset in subsets:
        total_imgs = sum(summary[subset]["images"].values())
        total_anns = sum(summary[subset]["annotations"].values())
        print(f"\nSubset: {subset.upper()}")
        for split in splits:
            imgs = summary[subset]["images"].get(split, 0)
            anns = summary[subset]["annotations"].get(split, 0)
            ratio = anns / imgs if imgs > 0 else 0
            print(f"  [{split.upper():5s}] Images: {imgs:5d} | Annotations: {anns:5d} | Mean/Image: {ratio:.2f}")
        print(f"  [TOTAL] Images: {total_imgs:5d} | Annotations: {total_anns:5d}")

    # ==========================================
    # Plot 1: Split Distribution
    # ==========================================
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(len(splits))
    width = 0.35

    # Images
    stenosis_imgs = [summary["stenosis"]["images"].get(s, 0) for s in splits]
    syntax_imgs = [summary["syntax"]["images"].get(s, 0) for s in splits]
    axes[0].bar(x - width/2, stenosis_imgs, width, label="Stenosis Task", color="#2B6CB0")
    axes[0].bar(x + width/2, syntax_imgs, width, label="Syntax Task", color="#4299E1")
    axes[0].set_title("Image Count by Split Partition", fontsize=12, fontweight="bold")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([s.capitalize() for s in splits])
    axes[0].set_ylabel("Number of Images")
    axes[0].legend()

    # Annotations
    stenosis_anns = [summary["stenosis"]["annotations"].get(s, 0) for s in splits]
    syntax_anns = [summary["syntax"]["annotations"].get(s, 0) for s in splits]
    axes[1].bar(x - width/2, stenosis_anns, width, label="Stenosis Plaques", color="#E53E3E")
    axes[1].bar(x + width/2, syntax_anns, width, label="Syntax Vessel Segments", color="#3182CE")
    axes[1].set_title("Annotation Instances by Split Partition", fontsize=12, fontweight="bold")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels([s.capitalize() for s in splits])
    axes[1].set_ylabel("Annotation Count")
    axes[1].legend()

    plt.tight_layout()
    p1 = OUTPUT_PLOTS_DIR / "1_split_distribution.png"
    plt.savefig(p1, dpi=300)
    plt.close()
    print(f"Plot saved: {p1}")

    # ==========================================
    # Plot 2: Top Anatomical Categories in SYNTAX
    # ==========================================
    if syntax_category_counts:
        top_cats = sorted(syntax_category_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        labels = [syntax_category_names.get(cid, f"Cat {cid}") for cid, _ in top_cats]
        counts = [cnt for _, cnt in top_cats]

        plt.figure(figsize=(12, 6))
        bars = plt.barh(range(len(labels))[::-1], counts, color="#2B6CB0")
        plt.yticks(range(len(labels))[::-1], labels)
        plt.xlabel("Total Polygon Segmentations Across Dataset")
        plt.title("Top 15 Anatomical Artery Categories (AHA/SYNTAX)", fontsize=13, fontweight="bold")
        for bar in bars:
            w = bar.get_width()
            plt.text(w + 20, bar.get_y() + bar.get_height()/2, f"{int(w)}", va="center", fontsize=9)
        plt.tight_layout()
        p2 = OUTPUT_PLOTS_DIR / "2_syntax_top_categories.png"
        plt.savefig(p2, dpi=300)
        plt.close()
        print(f"Plot saved: {p2}")

    # ==========================================
    # Plot 3: Stenosis Bounding Box Distribution
    # ==========================================
    if stenosis_box_areas:
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        axes[0].hist(stenosis_box_areas, bins=40, color="#E53E3E", edgecolor="black", alpha=0.8)
        axes[0].set_title("Stenosis Bounding Box Area Distribution (px²)", fontsize=12, fontweight="bold")
        axes[0].set_xlabel("Box Area (px²)")
        axes[0].set_ylabel("Frequency")

        axes[1].hist([ar for ar in stenosis_aspect_ratios if ar < 5], bins=40, color="#805AD5", edgecolor="black", alpha=0.8)
        axes[1].set_title("Stenosis Bounding Box Aspect Ratio (Width / Height)", fontsize=12, fontweight="bold")
        axes[1].set_xlabel("Aspect Ratio")
        axes[1].set_ylabel("Frequency")

        plt.tight_layout()
        p3 = OUTPUT_PLOTS_DIR / "3_stenosis_box_distribution.png"
        plt.savefig(p3, dpi=300)
        plt.close()
        print(f"Plot saved: {p3}")

    # ==========================================
    # Plot 4: Pixel Intensity & CLAHE Enhancement
    # ==========================================
    sample_img_path = DATASET_ROOT / "stenosis" / "train" / "images" / "1.png"
    if sample_img_path.exists():
        from StenoVision.preprocessing.pipeline import apply_clahe
        raw_arr = np.array(Image.open(sample_img_path).convert("L"))
        clahe_arr = apply_clahe(raw_arr)

        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        axes[0, 0].imshow(raw_arr, cmap="gray")
        axes[0, 0].set_title("Raw Angiogram (1.png)", fontweight="bold")
        axes[0, 0].axis("off")

        axes[0, 1].imshow(clahe_arr, cmap="gray")
        axes[0, 1].set_title("CLAHE Contrast Enhanced", fontweight="bold")
        axes[0, 1].axis("off")

        axes[1, 0].hist(raw_arr.ravel(), bins=50, color="#4A5568", alpha=0.8)
        axes[1, 0].set_title("Raw Intensity Histogram")
        axes[1, 0].set_xlabel("Pixel Value (0-255)")
        axes[1, 0].set_ylabel("Count")

        axes[1, 1].hist(clahe_arr.ravel(), bins=50, color="#2B6CB0", alpha=0.8)
        axes[1, 1].set_title("CLAHE Intensity Histogram")
        axes[1, 1].set_xlabel("Pixel Value (0-255)")
        axes[1, 1].set_ylabel("Count")

        plt.tight_layout()
        p4 = OUTPUT_PLOTS_DIR / "4_pixel_intensity_and_clahe.png"
        plt.savefig(p4, dpi=300)
        plt.close()
        print(f"Plot saved: {p4}")

    print("\nEDA completed successfully! All plots written to:", OUTPUT_PLOTS_DIR.resolve())


if __name__ == "__main__":
    run_eda()
