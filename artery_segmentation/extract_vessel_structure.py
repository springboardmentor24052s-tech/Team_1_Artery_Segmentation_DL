
import cv2
import numpy as np
from pathlib import Path
from skimage.morphology import skeletonize


# --------------------------------------------------
# 1. Define folders
# --------------------------------------------------

BASE_DIR = Path(__file__).parent

INPUT_FOLDERS = {
    "unet": BASE_DIR / "outputs" / "postprocessing" / "unet_cleaned",
    "attention_unet": BASE_DIR / "outputs" / "postprocessing" / "attention_unet_cleaned",
}

OUTPUT_FOLDERS = {
    "unet": BASE_DIR / "outputs" / "vessel_structure" / "unet_centerlines",
    "attention_unet": BASE_DIR / "outputs" / "vessel_structure" / "attention_unet_centerlines",
}


# --------------------------------------------------
# 2. Extract centerline
# --------------------------------------------------

def extract_centerline(mask):

    # Convert binary mask to boolean
    binary_mask = mask > 127

    # Skeletonize the vessel mask
    skeleton = skeletonize(binary_mask)

    # Convert skeleton to image format
    centerline = skeleton.astype(np.uint8) * 255

    return centerline


# --------------------------------------------------
# 3. Process prediction folder
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

        # Read cleaned mask
        mask = cv2.imread(
            str(image_path),
            cv2.IMREAD_GRAYSCALE
        )

        if mask is None:
            print(f"Could not read: {image_path.name}")
            continue

        # Extract centerline
        centerline = extract_centerline(mask)

        # Save centerline
        output_path = output_folder / image_path.name

        cv2.imwrite(
            str(output_path),
            centerline
        )

        processed_count += 1

    print(f"\nModel: {model_name}")
    print(f"Processed images: {processed_count}")
    print(f"Output folder: {output_folder}")


# --------------------------------------------------
# 4. Main execution
# --------------------------------------------------

if __name__ == "__main__":

    print("Starting vessel centerline extraction...")

    for model_name in INPUT_FOLDERS:

        process_folder(
            model_name,
            INPUT_FOLDERS[model_name],
            OUTPUT_FOLDERS[model_name]
        )

    print("\nCenterline extraction completed!")
