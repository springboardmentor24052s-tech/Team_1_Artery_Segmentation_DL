"""
StenoVision - Faster R-CNN MobileNetV3-Large-FPN Stenosis Detector
==================================================================
Deep learning object detector for whole-image (512x512) coronary artery
stenosis localization. Returns bounding boxes [x1, y1, x2, y2], confidence
scores, and predicted labels.
"""

from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torchvision.models.detection as detection
from torchvision.models.detection.rpn import AnchorGenerator


def build_stenosis_detector(
    num_classes: int = 2,  # 0: Background, 1: Stenosis
    pretrained_backbone: bool = True,
    min_size: int = 512,
    max_size: int = 512,
) -> nn.Module:
    """
    Constructs Faster R-CNN with MobileNetV3-Large-FPN backbone tailored
    specifically for coronary artery lesion detection.
    """
    weights_backbone = "DEFAULT" if pretrained_backbone else None

    model = detection.fasterrcnn_mobilenet_v3_large_fpn(
        weights=None,
        weights_backbone=weights_backbone,
        num_classes=num_classes,
        min_size=min_size,
        max_size=max_size,
        box_score_thresh=0.05,
        box_nms_thresh=0.30,
        box_detections_per_img=10,
    )

    return model
