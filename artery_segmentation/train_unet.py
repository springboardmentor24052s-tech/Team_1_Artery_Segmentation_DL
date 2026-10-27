
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from artery_dataset import ArteryDataset
from unet_model import UNet


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs" / "unet"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BATCH_SIZE = 2
EPOCHS = 3
LEARNING_RATE = 1e-3


def dice_score_from_logits(logits, masks):
    predictions = (torch.sigmoid(logits) >= 0.5).float()

    intersection = (predictions * masks).sum(dim=(1, 2, 3))
    denominator = (
        predictions.sum(dim=(1, 2, 3))
        + masks.sum(dim=(1, 2, 3))
    )

    scores = (2 * intersection + 1e-7) / (denominator + 1e-7)
    return scores.mean().item()


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)

    train_dataset = ArteryDataset("train")
    val_dataset = ArteryDataset("val")

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    model = UNet().to(device)

    # BCE handles pixel classification; Dice loss helps with
    # the imbalance between artery and background pixels.
    bce_loss = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE
    )

    best_val_dice = -1.0

    for epoch in range(EPOCHS):
        start_time = time.time()
        model.train()
        train_loss_total = 0.0

        progress = tqdm(
            train_loader,
            desc=f"Epoch {epoch + 1}/{EPOCHS}"
        )

        for images, masks in progress:
            images = images.to(device)
            masks = masks.to(device)

            optimizer.zero_grad()

            logits = model(images)

            bce = bce_loss(logits, masks)

            probabilities = torch.sigmoid(logits)
            intersection = (probabilities * masks).sum()
            dice_loss = 1 - (
                (2 * intersection + 1e-7)
                / (
                    probabilities.sum()
                    + masks.sum()
                    + 1e-7
                )
            )

            loss = bce + dice_loss
            loss.backward()
            optimizer.step()

            train_loss_total += loss.item()
            progress.set_postfix(loss=f"{loss.item():.4f}")

        avg_train_loss = train_loss_total / len(train_loader)

        model.eval()
        val_dice_total = 0.0

        with torch.no_grad():
            for images, masks in val_loader:
                images = images.to(device)
                masks = masks.to(device)

                logits = model(images)
                val_dice_total += dice_score_from_logits(
                    logits, masks
                )

        avg_val_dice = val_dice_total / len(val_loader)
        elapsed = time.time() - start_time

        print(f"\nEpoch: {epoch + 1}/{EPOCHS}")
        print(f"Training loss: {avg_train_loss:.4f}")
        print(f"Validation Dice: {avg_val_dice:.4f}")
        print(f"Time: {elapsed / 60:.2f} minutes")

        if avg_val_dice > best_val_dice:
            best_val_dice = avg_val_dice

            torch.save(
                {
                    "epoch": epoch + 1,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_dice": best_val_dice,
                },
                OUTPUT_DIR / "best_unet.pth"
            )

            print("Best model checkpoint saved.")

    print("\nTraining finished.")
    print(f"Best validation Dice: {best_val_dice:.4f}")
    print("Checkpoint:", OUTPUT_DIR / "best_unet.pth")


if __name__ == "__main__":
    main()
