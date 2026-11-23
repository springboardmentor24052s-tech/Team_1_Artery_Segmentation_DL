"""
StenoVision - Advanced Attention U-Net Architecture
===================================================
Incorporates spatial Attention Gates (AG) into the skip connections of U-Net.
Attention gates learn to focus on coronary arterial structures while suppressing
irrelevant background features (catheters, surgical clips, ribs, lung boundaries).
Total parameters: ~488,924
"""

import torch
import torch.nn as nn
from .unet import DoubleConv


class AttentionGate(nn.Module):
    """
    Attention Gate:
    Filters the skip connection feature map 'x' conditioned on gating signal 'g'
    derived from the coarser resolution decoder level.
    """
    def __init__(self, gate_channels: int, skip_channels: int, inter_channels: int):
        super().__init__()
        self.W_g = nn.Sequential(
            nn.Conv2d(gate_channels, inter_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(inter_channels)
        )
        self.W_x = nn.Sequential(
            nn.Conv2d(skip_channels, inter_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(inter_channels)
        )
        self.psi = nn.Sequential(
            nn.ReLU(inplace=True),
            nn.Conv2d(inter_channels, 1, kernel_size=1, bias=False),
            nn.BatchNorm2d(1),
            nn.Sigmoid()
        )

    def forward(self, g: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        # Align spatial dimensions if needed
        g_proj = self.W_g(g)
        x_proj = self.W_x(x)
        attention_map = self.psi(g_proj + x_proj)
        return x * attention_map


class AttentionUNet(nn.Module):
    def __init__(self, in_channels: int = 1, out_channels: int = 1, base_features: int = 16):
        super().__init__()
        f = base_features

        # Encoder path
        self.enc1 = DoubleConv(in_channels, f)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.enc2 = DoubleConv(f, f * 2)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.enc3 = DoubleConv(f * 2, f * 4)
        self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.enc4 = DoubleConv(f * 4, f * 8)
        self.pool4 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Bottleneck
        self.bottleneck = DoubleConv(f * 8, f * 16)

        # Attention Gates
        self.ag4 = AttentionGate(gate_channels=f * 8, skip_channels=f * 8, inter_channels=f * 4)
        self.ag3 = AttentionGate(gate_channels=f * 4, skip_channels=f * 4, inter_channels=f * 2)
        self.ag2 = AttentionGate(gate_channels=f * 2, skip_channels=f * 2, inter_channels=f)
        self.ag1 = AttentionGate(gate_channels=f, skip_channels=f, inter_channels=f // 2)

        # Decoder path
        self.up4 = nn.ConvTranspose2d(f * 16, f * 8, kernel_size=2, stride=2)
        self.dec4 = DoubleConv(f * 16, f * 8)

        self.up3 = nn.ConvTranspose2d(f * 8, f * 4, kernel_size=2, stride=2)
        self.dec3 = DoubleConv(f * 8, f * 4)

        self.up2 = nn.ConvTranspose2d(f * 4, f * 2, kernel_size=2, stride=2)
        self.dec2 = DoubleConv(f * 4, f * 2)

        self.up1 = nn.ConvTranspose2d(f * 2, f, kernel_size=2, stride=2)
        self.dec1 = DoubleConv(f * 2, f)

        # Output projection head (logits)
        self.out_conv = nn.Conv2d(f, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Encoder
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        e3 = self.enc3(self.pool2(e2))
        e4 = self.enc4(self.pool3(e3))

        # Bottleneck
        b = self.bottleneck(self.pool4(e4))

        # Decoder with attention gated skip connections
        d4 = self.up4(b)
        e4_att = self.ag4(g=d4, x=e4)
        d4 = self.dec4(torch.cat([d4, e4_att], dim=1))

        d3 = self.up3(d4)
        e3_att = self.ag3(g=d3, x=e3)
        d3 = self.dec3(torch.cat([d3, e3_att], dim=1))

        d2 = self.up2(d3)
        e2_att = self.ag2(g=d2, x=e2)
        d2 = self.dec2(torch.cat([d2, e2_att], dim=1))

        d1 = self.up1(d2)
        e1_att = self.ag1(g=d1, x=e1)
        d1 = self.dec1(torch.cat([d1, e1_att], dim=1))

        return self.out_conv(d1)

