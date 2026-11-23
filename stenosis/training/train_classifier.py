"""
StenoVision - Multi-Task Stenosis Classifier & Severity Training
================================================================
Trains MultiTaskStenosisResNet18 on 128x128 coronary candidate patches:
1. Binary Stenosis Classification
2. 4-tier ACC/AHA Severity Classification
3. Continuous %DS Diameter Narrowing Regression
Uses GPU mixed precision and saves best checkpoint.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stenosis.data_prep.patch_dataset import StenosisPatchDataset
from stenosis.models.multi_task_resnet import MultiTaskStenosisResNet18


def train_classifier(
    data_root: Path,
    epochs: int = 5,
    batch_size: int = 16,
    lr: float = 1e-4,
    device_name: str = "cuda",
):
    # Ensure stdout handles characters cleanly
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    device = torch.device(device_name if torch.cuda.is_available() and device_name == "cuda" else "cpu")
    print(f"Training Multi-Task Stenosis Classifier on {device} ({torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'})...")

    # Datasets
    train_ds = StenosisPatchDataset(data_root=data_root, split="train", patch_size=128, augment=True)
    val_ds = StenosisPatchDataset(data_root=data_root, split="val", patch_size=128, augment=False)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0, pin_memory=(device.type == "cuda"))
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    # Model
    model = MultiTaskStenosisResNet18(in_channels=1, pretrained=False).to(device)

    # Losses
    criterion_bin = nn.CrossEntropyLoss()
    criterion_sev = nn.CrossEntropyLoss()
    criterion_reg = nn.SmoothL1Loss()

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    scaler = torch.amp.GradScaler("cuda", enabled=(device.type == "cuda"))

    ckpt_dir = PROJECT_ROOT / "stenosis" / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    best_val_acc = 0.0
    history = {"train_loss": [], "val_loss": [], "val_binary_acc": [], "val_severity_acc": [], "val_ds_mae": []}

    print("\n" + "=" * 70)
    print(f"{'Epoch':^7} | {'Train Loss':^10} | {'Val Loss':^10} | {'Bin Acc':^9} | {'Sev Acc':^9} | {'%DS MAE':^9} | {'Time':^7}")
    print("=" * 70)

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        model.train()
        running_loss = 0.0
        n_train = 0

        for patches, is_stenosis, sev_class, pct_ds in train_loader:
            patches = patches.to(device)
            is_stenosis = is_stenosis.to(device)
            sev_class = sev_class.to(device)
            pct_ds = pct_ds.to(device).unsqueeze(1)

            optimizer.zero_grad()
            with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                outputs = model(patches)
                loss_b = criterion_bin(outputs["binary_logits"], is_stenosis)
                loss_s = criterion_sev(outputs["severity_logits"], sev_class)
                loss_r = criterion_reg(outputs["pct_narrowing"], pct_ds)
                loss = loss_b + loss_s + 0.05 * loss_r

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item() * patches.size(0)
            n_train += patches.size(0)

        scheduler.step()
        train_loss = running_loss / max(1, n_train)

        # Validation
        model.eval()
        val_loss = 0.0
        n_val = 0
        correct_bin = 0
        correct_sev = 0
        total_mae = 0.0

        with torch.no_grad():
            for patches, is_stenosis, sev_class, pct_ds in val_loader:
                patches = patches.to(device)
                is_stenosis = is_stenosis.to(device)
                sev_class = sev_class.to(device)
                pct_ds = pct_ds.to(device).unsqueeze(1)

                with torch.amp.autocast("cuda", enabled=(device.type == "cuda")):
                    outputs = model(patches)
                    loss_b = criterion_bin(outputs["binary_logits"], is_stenosis)
                    loss_s = criterion_sev(outputs["severity_logits"], sev_class)
                    loss_r = criterion_reg(outputs["pct_narrowing"], pct_ds)
                    loss = loss_b + loss_s + 0.05 * loss_r

                val_loss += loss.item() * patches.size(0)
                n_val += patches.size(0)

                pred_bin = torch.argmax(outputs["binary_logits"], dim=1)
                pred_sev = torch.argmax(outputs["severity_logits"], dim=1)
                correct_bin += (pred_bin == is_stenosis).sum().item()
                correct_sev += (pred_sev == sev_class).sum().item()
                total_mae += torch.abs(outputs["pct_narrowing"] - pct_ds).sum().item()

        val_loss /= max(1, n_val)
        bin_acc = (correct_bin / max(1, n_val)) * 100.0
        sev_acc = (correct_sev / max(1, n_val)) * 100.0
        ds_mae = total_mae / max(1, n_val)
        elapsed = time.time() - t0

        history["train_loss"].append(round(train_loss, 4))
        history["val_loss"].append(round(val_loss, 4))
        history["val_binary_acc"].append(round(bin_acc, 2))
        history["val_severity_acc"].append(round(sev_acc, 2))
        history["val_ds_mae"].append(round(ds_mae, 2))

        is_best = sev_acc > best_val_acc
        star = " [BEST]" if is_best else ""
        print(f"{epoch:^7} | {train_loss:^10.4f} | {val_loss:^10.4f} | {bin_acc:^8.2f}% | {sev_acc:^8.2f}% | {ds_mae:^8.2f}% | {elapsed:^6.1f}s{star}")

        if is_best or epoch == 1:
            best_val_acc = sev_acc
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_severity_acc": sev_acc,
                "val_binary_acc": bin_acc,
                "val_ds_mae": ds_mae,
                "optimizer_state_dict": optimizer.state_dict(),
            }, ckpt_dir / "best_stenosis_classifier.pth")

    with open(ckpt_dir / "classifier_history.json", "w") as f:
        json.dump(history, f, indent=2)

    print("=" * 70)
    print(f"Training completed! Best Validation Severity Accuracy: {best_val_acc:.2f}%")
    print(f"Model saved to: {ckpt_dir / 'best_stenosis_classifier.pth'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--device", type=str, default="cuda")
    args = parser.parse_args()

    train_classifier(
        data_root=PROJECT_ROOT,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device_name=args.device,
    )

