"""
StenoVision - Native PyTorch Occlusion Sensitivity XAI Engine
=============================================================
Computes empirical feature sensitivity by systematically occluding local rectangular
patches with a neutral baseline and measuring the corresponding drop in model confidence.
"""

from typing import Optional, Tuple
import cv2
import numpy as np
import torch
import torch.nn as nn


class OcclusionSensitivity:
    """
    Sliding window occlusion sensitivity analysis for lesion patches.
    """

    def __init__(self, model: nn.Module):
        self.model = model

    def attribute(
        self,
        input_tensor: torch.Tensor,
        window_size: int = 16,
        stride: int = 8,
        target_category: Optional[int] = None,
        task_head: str = "severity_logits",
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes 2D occlusion sensitivity attribution map.

        Args:
            input_tensor: [1, C, H, W] patch tensor
            window_size: Size of square occlusion mask in pixels (default: 16)
            stride: Stride step size for sliding mask (default: 8)
            target_category: Class index to evaluate (None = argmax predicted class)
            task_head: Model task head ('severity_logits' or 'binary_logits')

        Returns:
            Tuple of:
            - occ_norm: [H, W] normalized attribution map in [0.0, 1.0]
            - occ_heatmap_bgr: [H, W, 3] Jet colormapped image
        """
        self.model.eval()

        with torch.no_grad():
            orig_outputs = self.model(input_tensor)
            orig_logits = orig_outputs[task_head]

            if target_category is None:
                target_category = int(torch.argmax(orig_logits, dim=1).item())

            base_prob = torch.softmax(orig_logits, dim=1)[0, target_category].item()

            _, C, H, W = input_tensor.shape
            sensitivity_map = np.zeros((H, W), dtype=np.float32)
            count_map = np.zeros((H, W), dtype=np.float32)

            # Slide occlusion window across patch
            for y in range(0, H - window_size + 1, stride):
                for x in range(0, W - window_size + 1, stride):
                    occluded_input = input_tensor.clone()
                    # Neutral occlusion: local mean or zero
                    occluded_input[:, :, y : y + window_size, x : x + window_size] = 0.0

                    occ_outputs = self.model(occluded_input)
                    occ_logits = occ_outputs[task_head]
                    occ_prob = torch.softmax(occ_logits, dim=1)[0, target_category].item()

                    # Drop in probability indicates region importance
                    prob_drop = max(0.0, base_prob - occ_prob)
                    sensitivity_map[y : y + window_size, x : x + window_size] += prob_drop
                    count_map[y : y + window_size, x : x + window_size] += 1.0

            # Normalize overlapping counts
            count_map[count_map == 0] = 1.0
            avg_sensitivity = sensitivity_map / count_map

            # Min-max normalization
            s_min, s_max = avg_sensitivity.min(), avg_sensitivity.max()
            if s_max - s_min > 1e-8:
                occ_norm = (avg_sensitivity - s_min) / (s_max - s_min)
            else:
                occ_norm = np.zeros_like(avg_sensitivity)

            occ_uint8 = np.uint8(255 * occ_norm)
            occ_heatmap_bgr = cv2.applyColorMap(occ_uint8, cv2.COLORMAP_JET)

            return occ_norm.astype(np.float32), occ_heatmap_bgr

