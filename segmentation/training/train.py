"""
StenoVision - Model Training & Checkpointing Engine
===================================================
Usage:
    python train.py --model unet --epochs 5 --batch_size 4
    python train.py --model attention_unet --epochs 5 --batch_size 4
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

# Support UTF-8 in Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent
for p in [str(WORKSPACE_ROOT), str(PROJECT_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from StenoVision.segmentation.models import UNet, AttentionUNet
from StenoVision.segmentation.training.dataset import ArterySegmentationDataset
from StenoVision.segmentation.training.losses import DiceBCELoss


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MASKS_ROOT = PROJECT_ROOT / "data" / "masks"
CHECKPOINT_DIR = PROJECT_ROOT / "segmentation" / "checkpoints"


def calculate_dice(logits: torch.Tensor, targets: torch.Tensor, threshold: float = 0.5) -> float:
    probs = torch.sigmoid(logits)
    preds = (probs >= threshold).float()
    intersection = (preds * targets).sum(dim=(1, 2, 3))
    denominator = preds.sum(dim=(1, 2, 3)) + targets.sum(dim=(1, 2, 3))
    scores = (2.0 * intersection + 1e-7) / (denominator + 1e-7)
    return scores.mean().item()


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.cuda.amp.GradScaler,
    device: torch.device,
) -> Tuple[float, float]:
    model.train()
    running_loss = 0.0
    running_dice = 0.0

    pbar = tqdm(dataloader, desc="Training", leave=False)
    for images, masks, _ in pbar:
        images = images.to(device, non_blocking=True)
        masks = masks.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)

        with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
            outputs = model(images)
            loss = criterion(outputs, masks)

        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        dice = calculate_dice(outputs.detach(), masks)
        running_loss += loss.item()
        running_dice += dice
        pbar.set_postfix({"Loss": f"{loss.item():.4f}", "Dice": f"{dice:.4f}"})

    n = len(dataloader)
    return running_loss / n, running_dice / n


@torch.no_grad()
def evaluate_validation(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, float]:
    model.eval()
    running_loss = 0.0
    running_dice = 0.0

    for images, masks, _ in dataloader:
        images = images.to(device, non_blocking=True)
        masks = masks.to(device, non_blocking=True)

        with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
            outputs = model(images)
            loss = criterion(outputs, masks)

        dice = calculate_dice(outputs, masks)
        running_loss += loss.item()
        running_dice += dice

    n = len(dataloader)
    return running_loss / n, running_dice / n


def run_training(
    model_name: str = "unet",
    epochs: int = 5,
    batch_size: int = 4,
    lr: float = 1e-3,
    num_workers: int = 0,
):
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("=" * 70)
    print(f"StenoVision: Training {model_name.upper()} Architecture")
    print(f"Device: {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})")
    print(f"Epochs: {epochs} | Batch size: {batch_size} | Learning rate: {lr}")
    print("=" * 70)

    # Initialize model
    if model_name.lower() == "unet":
        model = UNet(in_channels=1, out_channels=1).to(device)
    elif model_name.lower() in ("attention_unet", "attentionunet"):
        model = AttentionUNet(in_channels=1, out_channels=1).to(device)
    else:
        raise ValueError(f"Unknown model name: {model_name}")

    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Trainable parameters: {total_params:,}")

    # Datasets and Loaders
    train_manifest = MASKS_ROOT / "train_manifest.json"
    val_manifest = MASKS_ROOT / "val_manifest.json"

    train_ds = ArterySegmentationDataset(train_manifest, augment=True, use_clahe=True)
    val_ds = ArterySegmentationDataset(val_manifest, augment=False, use_clahe=True)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=(device.type == "cuda"))
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=(device.type == "cuda"))

    print(f"Train samples: {len(train_ds)} ({len(train_loader)} batches)")
    print(f"Val samples:   {len(val_ds)} ({len(val_loader)} batches)")

    criterion = DiceBCELoss(bce_weight=0.5, dice_weight=1.0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    scaler = torch.amp.GradScaler("cuda", enabled=(device.type == "cuda"))

    history = {
        "model": model_name,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "total_parameters": total_params,
        "train_loss": [],
        "train_dice": [],
        "val_loss": [],
        "val_dice": [],
        "best_val_dice": 0.0,
        "training_time_seconds": 0.0,
    }

    best_val_dice = 0.0
    best_weights_path = CHECKPOINT_DIR / f"best_{model_name.lower()}.pth"
    start_time = time.time()

    for epoch in range(1, epochs + 1):
        ep_start = time.time()
        train_loss, train_dice = train_one_epoch(model, train_loader, criterion, optimizer, scaler, device)
        val_loss, val_dice = evaluate_validation(model, val_loader, criterion, device)
        scheduler.step()
        ep_duration = time.time() - ep_start

        history["train_loss"].append(train_loss)
        history["train_dice"].append(train_dice)
        history["val_loss"].append(val_loss)
        history["val_dice"].append(val_dice)

        is_best = val_dice > best_val_dice
        if is_best:
            best_val_dice = val_dice
            history["best_val_dice"] = best_val_dice
            torch.save({
                "epoch": epoch,
                "model_name": model_name,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_dice": val_dice,
                "val_loss": val_loss,
            }, best_weights_path)

        star = " [BEST]" if is_best else ""
        print(
            f"Epoch [{epoch:02d}/{epochs:02d}] ({ep_duration:4.1f}s) | "
            f"Train Loss: {train_loss:.4f} - Dice: {train_dice:.4f} | "
            f"Val Loss: {val_loss:.4f} - Dice: {val_dice:.4f}{star}"
        )

    total_time = time.time() - start_time
    history["training_time_seconds"] = total_time
    print("-" * 70)
    print(f"Training finished in {total_time:.1f}s | Best Val Dice: {best_val_dice:.4f}")
    print(f"Saved best checkpoint to: {best_weights_path}")

    # Save history
    hist_path = CHECKPOINT_DIR / f"{model_name.lower()}_history.json"
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    return history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StenoVision Model Trainer")
    parser.add_argument("--model", type=str, default="unet", choices=["unet", "attention_unet"], help="Model architecture")
    parser.add_argument("--epochs", type=int, default=5, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    args = parser.parse_args()

    run_training(
        model_name=args.model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
    )
