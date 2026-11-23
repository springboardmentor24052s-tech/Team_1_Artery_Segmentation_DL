"""
StenoVision - Multi-Task ResNet-18 for Stenosis Classification, Severity & XAI
==============================================================================
Processes 128x128 cropped coronary arterial candidate patches.
Outputs:
1. Binary Stenosis Presence: Logits [B, 2]
2. ACC/AHA Severity Grade: Logits [B, 4] (Normal, Mild, Moderate, Severe)
3. Percentage Diameter Stenosis (%DS): Continuous scalar [B, 1] in [0, 100]%
Exposes target convolutional layer for seamless Grad-CAM visual explanations.
"""

from typing import Dict, Tuple
import torch
import torch.nn as nn
import torchvision.models as models


class SpatialAttention(nn.Module):
    """Spatial attention module to focus on intraluminal filling defects."""
    def __init__(self, in_channels: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels // 2, kernel_size=1, bias=False),
            nn.BatchNorm2d(in_channels // 2),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels // 2, 1, kernel_size=1, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        att = self.conv(x)
        return x * att


class MultiTaskStenosisResNet18(nn.Module):
    def __init__(self, in_channels: int = 1, pretrained: bool = False):
        super().__init__()

        # ResNet-18 base
        base = models.resnet18(weights=None)

        # Adapt first conv layer if single-channel grayscale
        if in_channels != 3:
            self.first_conv = nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)
        else:
            self.first_conv = base.conv1

        self.bn1 = base.bn1
        self.relu = base.relu
        self.maxpool = base.maxpool

        self.layer1 = base.layer1
        self.layer2 = base.layer2
        self.layer3 = base.layer3
        self.layer4 = base.layer4  # Target layer for Grad-CAM

        self.spatial_att = SpatialAttention(512)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))

        # Multi-task heads
        feature_dim = 512
        # 1. Binary presence (Normal=0, Stenosis=1)
        self.binary_head = nn.Sequential(
            nn.Linear(feature_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, 2),
        )

        # 2. ACC/AHA Severity Grade (0: Normal, 1: Mild, 2: Moderate, 3: Severe)
        self.severity_head = nn.Sequential(
            nn.Linear(feature_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, 4),
        )

        # 3. Continuous %DS Narrowing Regression
        self.regression_head = nn.Sequential(
            nn.Linear(feature_dim, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(128, 1),
            nn.Sigmoid(),  # Output in [0, 1], multiplied by 100
        )

    def get_gradcam_target_layer(self) -> nn.Module:
        """Returns the final convolutional layer for Grad-CAM gradient calculation."""
        return self.layer4[1].conv2

    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        x = self.first_conv(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        x = self.spatial_att(x)
        return x

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        feat_map = self.extract_features(x)
        pooled = self.avgpool(feat_map)
        flat = torch.flatten(pooled, 1)

        binary_logits = self.binary_head(flat)
        severity_logits = self.severity_head(flat)
        pct_reg = self.regression_head(flat) * 100.0  # Scale to [0, 100]%

        return {
            "binary_logits": binary_logits,
            "severity_logits": severity_logits,
            "pct_narrowing": pct_reg,
            "feature_map": feat_map,
        }

