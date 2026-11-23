"""
StenoVision - Native PyTorch Grad-CAM Explainable AI Engine
===========================================================
Generates Gradient-Weighted Class Activation Maps (Grad-CAM) to visualize
the visual features (filling defects, eccentric plaques, caliber steps)
influencing the deep neural network's lesion detection and severity decisions.
Completely standalone with zero external third-party library dependencies.
"""

from typing import Optional, Tuple
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class GradCAM:
    """
    Native PyTorch Grad-CAM implementation.
    """

    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.gradients: Optional[torch.Tensor] = None
        self.activations: Optional[torch.Tensor] = None

        # Register forward and backward hooks
        self._fwd_hook = target_layer.register_forward_hook(self._save_activation)
        self._bwd_hook = target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input, output):
        self.activations = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_category: Optional[int] = None,
        task_head: str = "severity_logits",
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Computes Grad-CAM 2D heatmap.

        Args:
            input_tensor: [1, C, H, W] tensor with requires_grad=True
            target_category: Class index to explain (None = argmax predicted class)
            task_head: Which head output to backpropagate ('severity_logits' or 'binary_logits')

        Returns:
            Tuple of:
            - cam_norm: [H, W] float32 in [0.0, 1.0]
            - heatmap_bgr: [H, W, 3] uint8 colormapped image
        """
        self.model.eval()
        self.model.zero_grad()

        input_tensor = input_tensor.clone().requires_grad_(True)
        outputs = self.model(input_tensor)

        logits = outputs[task_head]  # [1, NumClasses]

        if target_category is None:
            target_category = int(torch.argmax(logits, dim=1).item())

        score = logits[0, target_category]
        score.backward(retain_graph=True)

        if self.gradients is None or self.activations is None:
            raise RuntimeError("Grad-CAM hooks failed to capture gradients or activations.")

        # Global average pooling of gradients: [1, K, 1, 1]
        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)

        # Weighted combination of forward activation maps
        cam = torch.sum(weights * self.activations, dim=1, keepdim=True)
        # Apply ReLU to retain only positive influences on class score
        cam = F.relu(cam)

        # Upsample to input patch resolution
        cam = F.interpolate(
            cam,
            size=(input_tensor.shape[2], input_tensor.shape[3]),
            mode="bilinear",
            align_corners=False,
        )

        cam_np = cam.squeeze().cpu().numpy()

        # Min-max normalization
        c_min, c_max = cam_np.min(), cam_np.max()
        if c_max - c_min > 1e-8:
            cam_norm = (cam_np - c_min) / (c_max - c_min)
        else:
            cam_norm = np.zeros_like(cam_np)

        # Generate Jet colormap
        cam_uint8 = np.uint8(255 * cam_norm)
        heatmap_bgr = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)

        return cam_norm, heatmap_bgr

    def generate_cam(
        self,
        input_tensor: torch.Tensor,
        target_head: str = "severity",
        class_idx: Optional[int] = None,
    ) -> np.ndarray:
        """Compatibility helper returning normalized 2D heatmap numpy array."""
        head_key = "severity_logits" if "sev" in target_head.lower() else "binary_logits"
        cam_norm, _ = self.generate_heatmap(
            input_tensor, target_category=class_idx, task_head=head_key
        )
        return cam_norm

    def remove_hooks(self):
        """Detaches PyTorch hooks."""
        self._fwd_hook.remove()
        self._bwd_hook.remove()


def overlay_gradcam_on_image(
    image_gray: np.ndarray,
    heatmap_bgr: np.ndarray,
    alpha: float = 0.55,
) -> np.ndarray:
    """Blends Grad-CAM heatmap over grayscale angiogram image."""
    if len(image_gray.shape) == 2:
        base_bgr = cv2.cvtColor(image_gray, cv2.COLOR_GRAY2BGR)
    else:
        base_bgr = image_gray.copy()

    if base_bgr.shape[:2] != heatmap_bgr.shape[:2]:
        heatmap_bgr = cv2.resize(heatmap_bgr, (base_bgr.shape[1], base_bgr.shape[0]))

    overlay = cv2.addWeighted(base_bgr, 1.0 - alpha, heatmap_bgr, alpha, 0)
    return overlay

