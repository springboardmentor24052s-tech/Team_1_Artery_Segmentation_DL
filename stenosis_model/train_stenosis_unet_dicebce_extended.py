from pathlib import Path
import random
import sys

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

MODEL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODEL_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stenosis_dataset import StenosisDataset
from stenosis_unet import StenosisUNet

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

BATCH_SIZE = 1
LEARNING_RATE = 0.0001
NUM_EPOCHS = 30
NUM_WORKERS = 0
EARLY_STOPPING_PATIENCE = 7
SCHEDULER_PATIENCE = 3
LR_FACTOR = 0.5
MIN_LEARNING_RATE = 1e-6

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
OUTPUT_DIR = MODEL_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BEST_MODEL_PATH = OUTPUT_DIR / "best_stenosis_unet_dicebce_extended.pth"


class DiceBCELoss(nn.Module):
    def __init__(self, smooth=1e-6):
        super().__init__()
        self.bce = nn.BCEWithLogitsLoss()
        self.smooth = smooth

    def forward(self, logits, targets):
        bce_loss = self.bce(logits, targets)
        probabilities = torch.sigmoid(logits)
        intersection = (probabilities * targets).sum(dim=(1, 2, 3))
        denominator = probabilities.sum(dim=(1, 2, 3)) + targets.sum(dim=(1, 2, 3))
        dice = (2.0 * intersection + self.smooth) / (denominator + self.smooth)
        return bce_loss + (1.0 - dice.mean())


@torch.no_grad()
def calculate_dice(logits, targets, threshold=0.5):
    predictions = (torch.sigmoid(logits) >= threshold).float()
    intersection = (predictions * targets).sum(dim=(1, 2, 3))
    denominator = predictions.sum(dim=(1, 2, 3)) + targets.sum(dim=(1, 2, 3))
    return ((2.0 * intersection + 1e-6) / (denominator + 1e-6)).mean().item()


def train_one_epoch(model, loader, optimizer, criterion, epoch):
    model.train()
    total_loss = 0.0
    total_dice = 0.0
    progress = tqdm(loader, desc=f"Epoch {epoch}/{NUM_EPOCHS} - Training")

    for images, masks in progress:
        images, masks = images.to(DEVICE), masks.to(DEVICE)
        optimizer.zero_grad(set_to_none=True)
        logits = model(images)
        loss = criterion(logits, masks)
        loss.backward()
        optimizer.step()

        dice = calculate_dice(logits.detach(), masks)
        total_loss += loss.item()
        total_dice += dice
        progress.set_postfix(loss=f"{loss.item():.4f}", dice=f"{dice:.4f}")

    return total_loss / len(loader), total_dice / len(loader)


@torch.no_grad()
def validate(model, loader, criterion, epoch):
    model.eval()
    total_loss = 0.0
    total_dice = 0.0
    progress = tqdm(loader, desc=f"Epoch {epoch}/{NUM_EPOCHS} - Validation")

    for images, masks in progress:
        images, masks = images.to(DEVICE), masks.to(DEVICE)
        logits = model(images)
        loss = criterion(logits, masks)
        dice = calculate_dice(logits, masks)
        total_loss += loss.item()
        total_dice += dice
        progress.set_postfix(loss=f"{loss.item():.4f}", dice=f"{dice:.4f}")

    return total_loss / len(loader), total_dice / len(loader)


def main():
    print("=" * 65)
    print("STENOSIS U-NET - EXTENDED BCE + DICE TRAINING")
    print("=" * 65)
    print("Device:", DEVICE)
    print("Batch size:", BATCH_SIZE)
    print("Initial learning rate:", LEARNING_RATE)
    print("Maximum epochs:", NUM_EPOCHS)
    print("Early stopping patience:", EARLY_STOPPING_PATIENCE)
    print("Loss: BCEWithLogitsLoss + Soft Dice Loss")
    print("Validation/checkpoint Dice threshold: 0.50")
    print("Checkpoint:", BEST_MODEL_PATH)

    if BEST_MODEL_PATH.exists():
        raise FileExistsError(
            f"Checkpoint already exists: {BEST_MODEL_PATH}\n"
            "It will not be overwritten. Rename it or change BEST_MODEL_PATH before rerunning."
        )

    print("\nLoading datasets...")
    train_dataset = StenosisDataset(split="train")
    val_dataset = StenosisDataset(split="val")
    if len(train_dataset) == 0 or len(val_dataset) == 0:
        raise RuntimeError("Training or validation dataset is empty.")

    train_loader = DataLoader(
        train_dataset, batch_size=BATCH_SIZE, shuffle=True,
        num_workers=NUM_WORKERS, pin_memory=(DEVICE.type == "cuda")
    )
    val_loader = DataLoader(
        val_dataset, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=NUM_WORKERS, pin_memory=(DEVICE.type == "cuda")
    )

    print("Training images:", len(train_dataset))
    print("Validation images:", len(val_dataset))

    model = StenosisUNet(in_channels=1, out_channels=1, base_channels=16).to(DEVICE)
    criterion = DiceBCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=LR_FACTOR,
        patience=SCHEDULER_PATIENCE, min_lr=MIN_LEARNING_RATE
    )

    best_val_dice = -1.0
    epochs_without_improvement = 0

    print("\nStarting training...\n")
    for epoch in range(1, NUM_EPOCHS + 1):
        train_loss, train_dice = train_one_epoch(
            model, train_loader, optimizer, criterion, epoch
        )
        val_loss, val_dice = validate(model, val_loader, criterion, epoch)

        old_lr = optimizer.param_groups[0]["lr"]
        scheduler.step(val_dice)
        current_lr = optimizer.param_groups[0]["lr"]

        print(f"\nEpoch {epoch}/{NUM_EPOCHS}")
        print(f"Train Loss: {train_loss:.4f} | Train Dice: {train_dice:.4f}")
        print(f"Val Loss:   {val_loss:.4f} | Val Dice:   {val_dice:.4f}")
        print(f"Learning rate: {current_lr:.7f}")
        if current_lr < old_lr:
            print("Learning rate reduced.")

        if val_dice > best_val_dice:
            best_val_dice = val_dice
            epochs_without_improvement = 0
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict(),
                "val_dice": val_dice,
                "val_loss": val_loss,
                "image_size": 512,
                "base_channels": 16,
                "loss_function": "BCEWithLogitsLoss + Soft Dice Loss",
                "learning_rate": LEARNING_RATE,
                "best_learning_rate": current_lr,
                "threshold": 0.5,
                "seed": SEED,
            }, BEST_MODEL_PATH)
            print("Saved new best checkpoint:", BEST_MODEL_PATH)
        else:
            epochs_without_improvement += 1
            print(
                f"No validation Dice improvement: "
                f"{epochs_without_improvement}/{EARLY_STOPPING_PATIENCE}"
            )

        print("-" * 65)
        if epochs_without_improvement >= EARLY_STOPPING_PATIENCE:
            print("\nEarly stopping: validation Dice did not improve.")
            break

    print("\nTraining completed.")
    print(f"Best validation Dice: {best_val_dice:.4f}")
    print("Best checkpoint:", BEST_MODEL_PATH)


if __name__ == "__main__":
    main()
