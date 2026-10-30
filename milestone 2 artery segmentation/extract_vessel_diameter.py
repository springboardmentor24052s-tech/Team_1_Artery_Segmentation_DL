"""Estimate vessel diameter along extracted centerlines from binary vessel masks.

The local diameter estimate at each centerline pixel is 2 * distance-to-background,
using an Euclidean distance transform of the segmented vessel mask.

Default inputs:
  outputs/postprocessing/unet_cleaned/
  outputs/postprocessing/attention_unet_cleaned/
  outputs/vessel_structure/unet_centerlines/ (if present)
  outputs/vessel_structure/attention_unet_centerlines/ (if present)

Outputs in outputs/vessel_diameter/:
  <model>_diameter_overlays/  - color-coded centerline diameter overlay PNGs
  <model>_diameter_maps/      - grayscale diameter maps (0 off centerline)
  diameter_profile.csv        - one row per centerline pixel (diameter in pixels)
  diameter_summary.csv        - per-image summary statistics (diameter in pixels)

Run:
  python extract_vessel_diameter.py
  python extract_vessel_diameter.py --model attention_unet
  python extract_vessel_diameter.py --model attention_unet --pixel-size-mm 0.0125

Physical units are only meaningful if --pixel-size-mm is based on valid image calibration.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np
from skimage.morphology import skeletonize

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUTS = {
    "unet": BASE_DIR / "outputs" / "postprocessing" / "unet_cleaned",
    "attention_unet": BASE_DIR / "outputs" / "postprocessing" / "attention_unet_cleaned",
}
STRUCTURE_ROOT = BASE_DIR / "outputs" / "vessel_structure"
OUTPUT_ROOT = BASE_DIR / "outputs" / "vessel_diameter"
EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def natural_sort_key(path: Path):
    return (0, int(path.stem)) if path.stem.isdigit() else (1, path.stem.lower())


def read_binary_mask(path: Path, threshold: int) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return image > threshold


def load_or_extract_centerline(mask_binary: np.ndarray, centerline_path: Path | None,
                               threshold: int) -> np.ndarray:
    if centerline_path is not None and centerline_path.exists():
        image = cv2.imread(str(centerline_path), cv2.IMREAD_GRAYSCALE)
        if image is not None and image.shape == mask_binary.shape:
            return image > threshold
    return skeletonize(mask_binary)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_cross_section_visualization(mask_binary: np.ndarray, centerline: np.ndarray,
                                      ys: np.ndarray, xs: np.ndarray,
                                      diameters_px: np.ndarray, output_path: Path,
                                      pixel_size_mm: float | None = None) -> None:
    """Draw perpendicular vessel-width measurements across the segmented mask.

    Green strokes show local cross-sections. One representative measurement near
    the median diameter is highlighted in red and labelled. Values are pixel units
    unless a calibrated mm-per-pixel value is supplied.
    """
    h, w = mask_binary.shape
    # White vessel mask on a black background, matching the requested visual style.
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    canvas[mask_binary] = (235, 235, 235)
    skeleton_yx = np.column_stack(np.where(centerline & mask_binary))
    if len(skeleton_yx) == 0:
        cv2.imwrite(str(output_path), canvas)
        return

    # Sample enough centerline points to make the width profile visible without
    # turning the image into a solid green patch.
    sample_step = max(1, int(np.ceil(len(skeleton_yx) / 160.0)))
    sampled = skeleton_yx[::sample_step]
    for y, x in sampled:
        nearby = skeleton_yx[(skeleton_yx[:, 0] - y) ** 2 + (skeleton_yx[:, 1] - x) ** 2 <= 100]
        if len(nearby) < 3:
            continue
        # PCA gives the local centerline tangent; its perpendicular is the cross-section.
        points = nearby[:, ::-1].astype(np.float32)  # x,y
        points -= points.mean(axis=0, keepdims=True)
        cov = points.T @ points
        vals, vecs = np.linalg.eigh(cov)
        tangent = vecs[:, int(np.argmax(vals))]
        normal = np.array([-tangent[1], tangent[0]], dtype=np.float32)
        # Walk from centerline to the mask boundary in both directions along the normal.
        endpoints = []
        for sign in (-1.0, 1.0):
            last = (int(x), int(y))
            for distance in range(1, 41):
                px = int(round(x + sign * normal[0] * distance))
                py = int(round(y + sign * normal[1] * distance))
                if px < 0 or py < 0 or px >= w or py >= h or not mask_binary[py, px]:
                    break
                last = (px, py)
            endpoints.append(last)
        p1, p2 = endpoints
        if p1 != p2:
            cv2.line(canvas, p1, p2, (40, 235, 40), 1, cv2.LINE_AA)

    # Highlight the centerline point whose diameter is closest to the median.
    if len(diameters_px):
        target = float(np.median(diameters_px))
        idx = int(np.argmin(np.abs(diameters_px - target)))
        y, x = int(ys[idx]), int(xs[idx])
        nearby = skeleton_yx[(skeleton_yx[:, 0] - y) ** 2 + (skeleton_yx[:, 1] - x) ** 2 <= 100]
        if len(nearby) >= 3:
            points = nearby[:, ::-1].astype(np.float32)
            points -= points.mean(axis=0, keepdims=True)
            vals, vecs = np.linalg.eigh(points.T @ points)
            tangent = vecs[:, int(np.argmax(vals))]
            normal = np.array([-tangent[1], tangent[0]], dtype=np.float32)
            endpoints = []
            for sign in (-1.0, 1.0):
                last = (x, y)
                for distance in range(1, 41):
                    px = int(round(x + sign * normal[0] * distance))
                    py = int(round(y + sign * normal[1] * distance))
                    if px < 0 or py < 0 or px >= w or py >= h or not mask_binary[py, px]:
                        break
                    last = (px, py)
                endpoints.append(last)
            cv2.line(canvas, endpoints[0], endpoints[1], (0, 0, 255), 2, cv2.LINE_AA)
            cv2.circle(canvas, (x, y), 3, (0, 0, 255), -1, cv2.LINE_AA)
        label_value = target * pixel_size_mm if pixel_size_mm is not None else target
        unit = 'mm' if pixel_size_mm is not None else 'px'
        label = f'{label_value:.2f} {unit}'
        tx, ty = min(max(x + 10, 5), max(5, w - 130)), min(max(y - 10, 20), h - 5)
        cv2.putText(canvas, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (0, 0, 255), 2, cv2.LINE_AA)

    cv2.putText(canvas, 'Green: local diameter | Red: median diameter', (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 220, 255), 1, cv2.LINE_AA)
    cv2.imwrite(str(output_path), canvas)


def process_model(model: str, input_dir: Path, pixel_size_mm: float | None,
                  threshold: int, min_diameter_px: float) -> tuple[list[dict], list[dict]]:
    if not input_dir.exists():
        print(f"[SKIP] {model}: mask folder not found: {input_dir}")
        return [], []
    files = sorted((p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS), key=natural_sort_key)
    if not files:
        print(f"[SKIP] {model}: no image masks found in {input_dir}")
        return [], []

    centerline_dir = STRUCTURE_ROOT / f"{model}_centerlines"
    overlay_dir = OUTPUT_ROOT / f"{model}_diameter_overlays"
    map_dir = OUTPUT_ROOT / f"{model}_diameter_maps"
    cross_section_dir = OUTPUT_ROOT / f"{model}_diameter_visualizations"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    map_dir.mkdir(parents=True, exist_ok=True)
    cross_section_dir.mkdir(parents=True, exist_ok=True)
    point_rows: list[dict] = []
    summary_rows: list[dict] = []

    for mask_path in files:
        try:
            mask_binary = read_binary_mask(mask_path, threshold)
        except ValueError as exc:
            print(f"[WARN] {exc}")
            continue
        centerline_path = centerline_dir / f"{mask_path.stem}.png"
        centerline = load_or_extract_centerline(mask_binary, centerline_path, threshold)
        # OpenCV distance transform returns the distance from each foreground pixel
        # to the nearest background pixel. Sampling on the skeleton estimates local radius.
        mask_u8 = mask_binary.astype(np.uint8)
        distance = cv2.distanceTransform(mask_u8, cv2.DIST_L2, 5)
        ys, xs = np.where(centerline & mask_binary)
        radii = distance[ys, xs].astype(np.float32)
        diameters_px = 2.0 * radii
        valid = np.isfinite(diameters_px) & (diameters_px >= min_diameter_px)
        ys, xs, radii, diameters_px = ys[valid], xs[valid], radii[valid], diameters_px[valid]

        diameters_units = diameters_px * pixel_size_mm if pixel_size_mm is not None else diameters_px
        for index, (y, x, radius, diameter, value) in enumerate(zip(ys, xs, radii, diameters_px, diameters_units), start=1):
            row = {
                "model": model,
                "image": mask_path.name,
                "point_index": index,
                "x_px": int(x),
                "y_px": int(y),
                "radius_px": round(float(radius), 4),
                "diameter_px": round(float(diameter), 4),
            }
            if pixel_size_mm is not None:
                row["diameter_mm"] = round(float(value), 6)
            point_rows.append(row)

        # Diameter map is zero except at centerline pixels; normalize to 8-bit for viewing.
        diameter_map = np.zeros(mask_binary.shape, dtype=np.float32)
        diameter_map[ys, xs] = diameters_px
        map_max = float(diameters_px.max()) if diameters_px.size else 0.0
        map_u8 = np.zeros(mask_binary.shape, dtype=np.uint8)
        if map_max > 0:
            map_u8 = np.clip(diameter_map / map_max * 255.0, 0, 255).astype(np.uint8)
        cv2.imwrite(str(map_dir / f"{mask_path.stem}.png"), map_u8)

        # Color-coded overlay: hue represents local diameter; vessel mask is a dim gray backdrop.
        gray = (mask_binary.astype(np.uint8) * 55)
        overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        if map_max > 0 and ys.size:
            color_values = np.clip(diameter_map / map_max * 255.0, 0, 255).astype(np.uint8)
            colored = cv2.applyColorMap(color_values, cv2.COLORMAP_TURBO)
            overlay[centerline & mask_binary] = colored[centerline & mask_binary]
        cv2.imwrite(str(overlay_dir / f"{mask_path.stem}.png"), overlay)

        # Requested visualization: white vessel on black with green perpendicular
        # diameter samples and a red median-diameter marker/label.
        make_cross_section_visualization(
            mask_binary, centerline, ys, xs, diameters_px,
            cross_section_dir / f"{mask_path.stem}.png", pixel_size_mm
        )

        if diameters_px.size:
            summary = {
                "model": model,
                "image": mask_path.name,
                "mask_width_px": int(mask_binary.shape[1]),
                "mask_height_px": int(mask_binary.shape[0]),
                "centerline_points_measured": int(diameters_px.size),
                "mean_diameter_px": round(float(np.mean(diameters_px)), 4),
                "median_diameter_px": round(float(np.median(diameters_px)), 4),
                "min_diameter_px": round(float(np.min(diameters_px)), 4),
                "max_diameter_px": round(float(np.max(diameters_px)), 4),
                "std_diameter_px": round(float(np.std(diameters_px)), 4),
                "diameter_overlay": str((overlay_dir / f"{mask_path.stem}.png").relative_to(BASE_DIR)),
                "diameter_map": str((map_dir / f"{mask_path.stem}.png").relative_to(BASE_DIR)),
                "diameter_visualization": str((cross_section_dir / f"{mask_path.stem}.png").relative_to(BASE_DIR)),
            }
            if pixel_size_mm is not None:
                summary.update({
                    "mean_diameter_mm": round(float(np.mean(diameters_px) * pixel_size_mm), 6),
                    "median_diameter_mm": round(float(np.median(diameters_px) * pixel_size_mm), 6),
                    "min_diameter_mm": round(float(np.min(diameters_px) * pixel_size_mm), 6),
                    "max_diameter_mm": round(float(np.max(diameters_px) * pixel_size_mm), 6),
                    "std_diameter_mm": round(float(np.std(diameters_px) * pixel_size_mm), 6),
                })
            summary_rows.append(summary)
        else:
            print(f"[WARN] No valid centerline points in {mask_path.name}")

    print(f"\nModel: {model}")
    print(f"Masks processed: {len(files)}")
    print(f"Per-point measurements: {len(point_rows)}")
    print(f"Diameter overlays: {overlay_dir}")
    print(f"Diameter maps: {map_dir}")
    return point_rows, summary_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate vessel diameter along centerlines from segmented vessel masks.")
    parser.add_argument("--model", choices=["unet", "attention_unet", "all"], default="all")
    parser.add_argument("--input", type=Path, default=None, help="Custom mask folder; use with a single --model.")
    parser.add_argument("--threshold", type=int, default=127, help="Mask foreground threshold (default: 127).")
    parser.add_argument("--pixel-size-mm", type=float, default=None, help="Optional calibrated mm per pixel; omit for pixel units only.")
    parser.add_argument("--min-diameter-px", type=float, default=0.1, help="Ignore measurements smaller than this diameter in pixels.")
    args = parser.parse_args()
    if args.pixel_size_mm is not None and args.pixel_size_mm <= 0:
        parser.error("--pixel-size-mm must be positive")
    if args.min_diameter_px < 0:
        parser.error("--min-diameter-px must be non-negative")
    models = ["unet", "attention_unet"] if args.model == "all" else [args.model]
    all_points: list[dict] = []
    all_summaries: list[dict] = []
    for model in models:
        input_dir = args.input if args.input is not None else DEFAULT_INPUTS[model]
        points, summaries = process_model(model, input_dir, args.pixel_size_mm, args.threshold, args.min_diameter_px)
        all_points.extend(points)
        all_summaries.extend(summaries)
    if all_points:
        point_fields = ["model", "image", "point_index", "x_px", "y_px", "radius_px", "diameter_px"]
        if args.pixel_size_mm is not None:
            point_fields.append("diameter_mm")
        write_csv(OUTPUT_ROOT / "diameter_profile.csv", all_points, point_fields)
    if all_summaries:
        summary_fields = list(all_summaries[0].keys())
        write_csv(OUTPUT_ROOT / "diameter_summary.csv", all_summaries, summary_fields)
    if not all_points:
        print("\nNo diameter measurements generated. Check cleaned mask folders and centerline outputs.")
    else:
        print(f"\nPoint measurements CSV: {OUTPUT_ROOT / 'diameter_profile.csv'}")
        print(f"Image summary CSV: {OUTPUT_ROOT / 'diameter_summary.csv'}")
        if args.pixel_size_mm is None:
            print("Units: pixels only. Use --pixel-size-mm only when you know the image calibration.")


if __name__ == "__main__":
    main()
