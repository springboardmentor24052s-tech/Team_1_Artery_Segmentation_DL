
from pathlib import Path
import sys

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

MODEL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODEL_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))

from stenosis_dataset import StenosisDataset
from stenosis_unet import StenosisUNet


# --------------------------------------------------
# TRAINING SETTINGS
# --------------------------------------------------

BATCH_SIZE = 1
LEARNING_RATE = 0.0001
NUM_EPOCHS = 5
NUM_WORKERS = 0

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

OUTPUT_DIR = MODEL_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Separate checkpoint.
# Existing model checkpoints will NOT be overwritten.
BEST_MODEL_PATH = (
    OUTPUT_DIR / "best_stenosis_unet_bce_control.pth"
)


# --------------------------------------------------
# DICE METRIC
# --------------------------------------------------

def calculate_dice(logits, targets):

    predictions = (
        torch.sigmoid(logits) >= 0.5
    ).float()

    smooth = 1e-6

    intersection = (
        predictions * targets
    ).sum(dim=(1, 2, 3))

    denominator = (
        predictions.sum(dim=(1, 2, 3))
        + targets.sum(dim=(1, 2, 3))
    )

    dice = (
        2.0 * intersection + smooth
    ) / (
        denominator + smooth
    )

    return dice.mean().item()


# --------------------------------------------------
# TRAINING FUNCTION
# --------------------------------------------------

def train_one_epoch(
    model,
    loader,
    optimizer,
    criterion,
    epoch
):

    model.train()

    total_loss = 0.0
    total_dice = 0.0

    progress = tqdm(
        loader,
        desc=f"Epoch {epoch}/{NUM_EPOCHS} - Training"
    )

    for images, masks in progress:

        images = images.to(DEVICE)
        masks = masks.to(DEVICE)

        optimizer.zero_grad(set_to_none=True)

        logits = model(images)

        loss = criterion(logits, masks)

        loss.backward()

        optimizer.step()

        dice = calculate_dice(
            logits.detach(),
            masks
        )

        total_loss += loss.item()
        total_dice += dice

        progress.set_postfix(
            loss=f"{loss.item():.4f}",
            dice=f"{dice:.4f}"
        )

    average_loss = total_loss / len(loader)
    average_dice = total_dice / len(loader)

    return average_loss, average_dice


# --------------------------------------------------
# VALIDATION FUNCTION
# --------------------------------------------------

@torch.no_grad()
def validate(
    model,
    loader,
    criterion,
    epoch
):

    model.eval()

    total_loss = 0.0
    total_dice = 0.0

    progress = tqdm(
        loader,
        desc=f"Epoch {epoch}/{NUM_EPOCHS} - Validation"
    )

    for images, masks in progress:

        images = images.to(DEVICE)
        masks = masks.to(DEVICE)

        logits = model(images)

        loss = criterion(logits, masks)

        dice = calculate_dice(
            logits,
            masks
        )

        total_loss += loss.item()
        total_dice += dice

        progress.set_postfix(
            loss=f"{loss.item():.4f}",
            dice=f"{dice:.4f}"
        )

    average_loss = total_loss / len(loader)
    average_dice = total_dice / len(loader)

    return average_loss, average_dice


# --------------------------------------------------
# MAIN TRAINING
# --------------------------------------------------

def main():

    print("=" * 60)
    print("STENOSIS U-NET - CONTROLLED BCE TRAINING")
    print("Loss Function: BCEWithLogitsLoss")
    print("=" * 60)

    print("Device:", DEVICE)
    print("Image resolution: 512 x 512")
    print("Batch size:", BATCH_SIZE)
    print("Learning rate:", LEARNING_RATE)
    print("Epochs:", NUM_EPOCHS)

    print("\nCheckpoint will be saved to:")
    print(BEST_MODEL_PATH)

    print("\nLoading datasets...")

    train_dataset = StenosisDataset(
        split="train"
    )

    val_dataset = StenosisDataset(
        split="val"
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=(DEVICE.type == "cuda")
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=(DEVICE.type == "cuda")
    )

    print("\nTraining images:", len(train_dataset))
    print("Validation images:", len(val_dataset))

    # Same U-Net architecture as the BCE + Dice run.
    model = StenosisUNet(
        in_channels=1,
        out_channels=1,
        base_channels=16
    ).to(DEVICE)

    # BCE ONLY - no Dice loss included.
    criterion = nn.BCEWithLogitsLoss()

    # Adam optimizer.
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE
    )

    best_val_dice = 0.0

    print("\nStarting BCE-only training...\n")

    for epoch in range(1, NUM_EPOCHS + 1):

        train_loss, train_dice = train_one_epoch(
            model,
            train_loader,
            optimizer,
            criterion,
            epoch
        )

        val_loss, val_dice = validate(
            model,
            val_loader,
            criterion,
            epoch
        )

        print(f"\nEpoch {epoch}/{NUM_EPOCHS}")

        print(f"Train Loss: {train_loss:.4f}")
        print(f"Train Dice: {train_dice:.4f}")

        print(f"Val Loss:   {val_loss:.4f}")
        print(f"Val Dice:   {val_dice:.4f}")

        # Save the model with the best validation Dice.
        if val_dice > best_val_dice:

            best_val_dice = val_dice

            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_dice": val_dice,
                    "image_size": 512,
                    "base_channels": 16,
                    "loss_function": "BCE",
                    "learning_rate": LEARNING_RATE,
                },
                BEST_MODEL_PATH
            )

            print(
                "\nBest BCE model saved:",
                BEST_MODEL_PATH
            )

        print("-" * 60)

    print("\nTraining completed.")

    print(
        f"Best validation Dice: {best_val_dice:.4f}"
    )

    print(
        "Best model location:",
        BEST_MODEL_PATH
    )


if __name__ == "__main__":
    main()
