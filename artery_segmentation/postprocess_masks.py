
import cv2
import numpy as np
from pathlib import Path


# --------------------------------------------------
# 1. Define input and output folders
# --------------------------------------------------

BASE_DIR = Path(__file__).parent

INPUT_FOLDERS = {
    "unet": BASE_DIR / "outputs" / "postprocessing" / "unet_raw",
    "attention_unet": BASE_DIR / "outputs" / "postprocessing" / "attention_unet_raw",
}

OUTPUT_FOLDERS = {
    "unet": BASE_DIR / "outputs" / "postprocessing" / "unet_cleaned",
    "attention_unet": BASE_DIR / "outputs" / "postprocessing" / "attention_unet_cleaned",
}


# --------------------------------------------------
# 2. Post-processing function
# --------------------------------------------------

def clean_mask(mask):

    # Convert image into binary mask
    _, binary = cv2.threshold(
        mask,
        127,
        255,
        cv2.THRESH_BINARY
    )

    # Remove small isolated components
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary,
        connectivity=8
    )

    cleaned = np.zeros_like(binary)

    # Keep components larger than the minimum area
    MIN_AREA = 50

    for label in range(1, num_labels):

        area = stats[label, cv2.CC_STAT_AREA]

        if area >= MIN_AREA:
            cleaned[labels == label] = 255

    # Fill small holes using morphological closing
    kernel = np.ones((3, 3), np.uint8)

    cleaned = cv2.morphologyEx(
        cleaned,
        cv2.MORPH_CLOSE,
        kernel
    )

    return cleaned


# --------------------------------------------------
# 3. Process prediction folders
# --------------------------------------------------

def process_folder(model_name, input_folder, output_folder):

    input_folder = Path(input_folder)
    output_folder = Path(output_folder)

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    image_files = sorted(
        input_folder.glob("*.png"),
        key=lambda path: int(path.stem) if path.stem.isdigit() else path.stem
    )

    if not image_files:
        print(f"No PNG images found in: {input_folder}")
        return

    processed_count = 0

    for image_path in image_files:

        # Read prediction mask
        mask = cv2.imread(
            str(image_path),
            cv2.IMREAD_GRAYSCALE
        )

        if mask is None:
            print(f"Could not read: {image_path.name}")
            continue

        # Apply post-processing
        cleaned_mask = clean_mask(mask)

        # Save cleaned mask
        output_path = output_folder / image_path.name

        cv2.imwrite(
            str(output_path),
            cleaned_mask
        )

        processed_count += 1

    print(f"\nModel: {model_name}")
    print(f"Input: {input_folder}")
    print(f"Output: {output_folder}")
    print(f"Processed images: {processed_count}")


# --------------------------------------------------
# 4. Main execution
# --------------------------------------------------

if __name__ == "__main__":

    print("Starting artery mask post-processing...")

    for model_name in INPUT_FOLDERS:

        process_folder(
            model_name,
            INPUT_FOLDERS[model_name],
            OUTPUT_FOLDERS[model_name]
        )

    print("\nPost-processing completed!")
