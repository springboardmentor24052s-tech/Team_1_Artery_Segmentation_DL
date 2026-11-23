"""
StenoVision - Native PyTorch Integrated Gradients XAI Engine
============================================================
Computes pixel-level attribution maps satisfying the axioms of Completeness
and Implementation Invariance. Measures the path-integral of gradients
along a straight trajectory from a neutral reference baseline to the input angiogram.
"""

from typing import Optional, Tuple
import cv2
import numpy as np
import torch
import torch.nn as nn


class IntegratedGradients:
    """
    Native PyTorch Integrated Gradients implementation for CNN patch classification.
    """

    def __init__(self, model: nn.Module):
        self.model = model

    def attribute(
        self,
        input_tensor: torch.Tensor,
        baseline: Optional[torch.Tensor] = None,
        target_category: Optional[int] = None,
        task_head: str = "severity_logits",
        steps: int = 20,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes Integrated Gradients attribution map.

        Args:
            input_tensor: [1, C, H, W] input image patch
            baseline: [1, C, H, W] baseline reference (defaults to zeros / blank scan)
            target_category: Class index to explain (None = argmax predicted class)
            task_head: Model task head to backpropagate ('severity_logits' or 'binary_logits')
            steps: Number of Riemann sum approximation steps (default: 20)

        Returns:
            Tuple of:
            - ig_norm: [H, W] normalized attribution map in [0.0, 1.0]
            - ig_heatmap_bgr: [H, W, 3] color-mapped Jet attribution heatmap
        """
        self.model.eval()

        if baseline is None:
            baseline = torch.zeros_like(input_tensor)

        # 1. Generate linearly interpolated inputs between baseline and input
        alphas = torch.linspace(0.0, 1.0, steps + 1, device=input_tensor.device)
        interpolated_inputs = [
            baseline + alpha * (input_tensor - baseline) for alpha in alphas
        ]

        total_gradients = torch.zeros_like(input_tensor)

        # 2. Compute gradients at each step along the path
        for interp_tensor in interpolated_inputs:
            interp_tensor = interp_tensor.clone().detach().requires_grad_(True)
            outputs = self.model(interp_tensor)
            logits = outputs[task_head]

            if target_category is None:
                target_category = int(torch.argmax(logits, dim=1).item())

            score = logits[0, target_category]
            self.model.zero_grad()
            score.backward()

            if interp_tensor.grad is not None:
                total_gradients += interp_tensor.grad.detach()

        # 3. Path integral approximation: (input - baseline) * average_gradient
        avg_gradients = total_gradients / (steps + 1)
        integrated_grad = (input_tensor - baseline) * avg_gradients

        # 4. Collapse channels if multi-channel (e.g. grayscale or 3-channel)
        ig_map = torch.mean(torch.abs(integrated_grad), dim=1).squeeze().cpu().numpy()

        # 5. Min-max normalization
        ig_min, ig_max = ig_map.min(), ig_map.max()
        if ig_max - ig_min > 1e-8:
            ig_norm = (ig_map - ig_min) / (ig_max - ig_min)
        else:
            ig_norm = np.zeros_like(ig_map)

        # 6. Apply Jet colormap (Red/Yellow = high attribution, Blue = low attribution)
        ig_uint8 = np.uint8(255 * ig_norm)
        ig_heatmap_bgr = cv2.applyColorMap(ig_uint8, cv2.COLORMAP_JET)

        return ig_norm.astype(np.float32), ig_heatmap_bgr

