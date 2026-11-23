"""
StenoVision - Faster R-CNN Stenosis Detector Training
=====================================================
Trains Faster R-CNN MobileNetV3-Large-FPN on 1,000 coronary angiograms
with 1,625 ground-truth stenosis lesions using RTX 2050 GPU mixed precision.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stenosis.data_prep.dataset_coco import CoronaryStenosisDataset, detection_collate_fn
from stenosis.models.detector import build_stenosis_detector


def train_detector(
    data_root: Path,
    epochs: int = 5,
    batch_size: int = 4,
    lr: float = 0.001,
    device_name: str = "cuda",
):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    device = torch.device(device_name if torch.cuda.is_available() and device_name == "cuda" else "cpu")
    print(f"Training Faster R-CNN Stenosis Detector on {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})...")

    # Datasets
    train_ds = CoronaryStenosisDataset(data_root=data_root, split="train", img_size=512)
    val_ds = CoronaryStenosisDataset(data_root=data_root, split="val", img_size=512)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=detection_collate_fn,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=detection_collate_fn,
        num_workers=0,
    )

    model = build_stenosis_detector(num_classes=2, pretrained_backbone=True).to(device)

    # Optimizer & Scheduler
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(params, lr=lr, momentum=0.9, weight_decay=0.0005)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    scaler = torch.amp.GradScaler("cuda", enabled=(device.type == "cuda"))

    ckpt_dir = PROJECT_ROOT / "stenosis" / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    best_val_loss = float("inf")
    history = {"train_loss": [], "val_loss": []}

    print("\n" + "=" * 65)
    print(f"{'Epoch':^7} | {'Train Loss':^14} | {'Val Loss':^14} | {'Time':^10}")
    print("=" * 65)

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        model.train()
        running_loss = 0.0
        n_batches = 0

        for images, targets in train_loader:
            images = [img.to(device) for img in images]
            targets = [{k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in t.items()} for t in targets]

            optimizer.zero_grad()
            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                loss_dict = model(images, targets)
                losses = sum(loss for loss in loss_dict.values())

            scaler.scale(losses).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += losses.item()
            n_batches += 1

        scheduler.step()
        train_loss = running_loss / max(1, n_batches)

        # Validation Loss
        # In torchvision Faster R-CNN, model.train() returns losses on both train and val batches!
        val_running_loss = 0.0
        val_batches = 0
        with torch.no_grad():
            for images, targets in val_loader:
                images = [img.to(device) for img in images]
                targets = [{k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in t.items()} for t in targets]

                with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                    loss_dict = model(images, targets)
                    val_losses = sum(loss for loss in loss_dict.values())

                val_running_loss += val_losses.item()
                val_batches += 1

        val_loss = val_running_loss / max(1, val_batches)
        elapsed = time.time() - t0

        history["train_loss"].append(round(train_loss, 4))
        history["val_loss"].append(round(val_loss, 4))

        is_best = val_loss < best_val_loss
        star = " [BEST]" if is_best else ""
        print(f"{epoch:^7} | {train_loss:^14.4f} | {val_loss:^14.4f} | {elapsed:^9.1f}s{star}")

        if is_best or epoch == 1:
            best_val_loss = val_loss
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_loss": val_loss,
                "train_loss": train_loss,
                "optimizer_state_dict": optimizer.state_dict(),
            }, ckpt_dir / "best_stenosis_detector.pth")

    with open(ckpt_dir / "detector_history.json", "w") as f:
        json.dump(history, f, indent=2)

    print("=" * 65)
    print(f"Training completed! Best Validation Loss: {best_val_loss:.4f}")
    print(f"Model saved to: {ckpt_dir / 'best_stenosis_detector.pth'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--device", type=str, default="cuda")
    args = parser.parse_args()

    train_detector(
        data_root=PROJECT_ROOT,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device_name=args.device,
    )

