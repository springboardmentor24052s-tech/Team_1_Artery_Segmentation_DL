"""
StenoVision - Segmentation Loss Functions
=========================================
Implements Dice Loss and Combined Dice-BCE Loss tailored for vessel segmentation.
Addresses heavy foreground-background class imbalance (vessels occupy ~5-8% of pixels).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DiceLoss(nn.Module):
    def __init__(self, smooth: float = 1.0):
        super().__init__()
        self.smooth = smooth

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.sigmoid(logits)
        probs_flat = probs.view(-1)
        targets_flat = targets.view(-1)

        intersection = (probs_flat * targets_flat).sum()
        denominator = probs_flat.sum() + targets_flat.sum()
        dice = (2.0 * intersection + self.smooth) / (denominator + self.smooth)
        return 1.0 - dice


class DiceBCELoss(nn.Module):
    """
    Combined Loss: alpha * BCE + beta * Dice
    Provides smooth cross-entropy gradient flow while directly optimizing Dice overlap.
    """
    def __init__(self, bce_weight: float = 0.5, dice_weight: float = 1.0, smooth: float = 1.0):
        super().__init__()
        self.bce_weight = bce_weight
        self.dice_weight = dice_weight
        self.dice = DiceLoss(smooth=smooth)
        self.bce = nn.BCEWithLogitsLoss()

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        bce_loss = self.bce(logits, targets)
        dice_loss = self.dice(logits, targets)
        return self.bce_weight * bce_loss + self.dice_weight * dice_loss

