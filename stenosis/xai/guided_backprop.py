"""
Sub-Team 3: Explainable AI & Visualization - Member 5
Module: Guided Backpropagation Saliency Generator
=================================================
Suppresses negative gradients during backpropagation to highlight
fine vascular lumen boundaries and high-frequency edge attributions.
"""

import torch
import torch.nn as nn
import numpy as np


class GuidedBackprop:
    """Guided Backpropagation implementation for PyTorch CNN backbones."""

    def __init__(self, model: nn.Module):
        self.model = model
        self.hooks = []
        self._register_hooks()

    def _register_hooks(self):
        def relu_backward_hook_function(module, grad_in, grad_out):
            # Only propagate positive gradients through positive activations
            if isinstance(module, nn.ReLU):
                return (torch.clamp(grad_in[0], min=0.0),)

        for module in self.model.modules():
            if isinstance(module, nn.ReLU):
                hook = module.register_full_backward_hook(relu_backward_hook_function)
                self.hooks.append(hook)

    def generate_saliency(self, input_patch: torch.Tensor, target_class: int = 2) -> np.ndarray:
        self.model.zero_grad()
        patch = input_patch.clone().detach().requires_grad_(True)
        outputs = self.model(patch)
        logits = outputs.get("severity_logits", outputs.get("severity", None))
        if logits is None:
            return np.zeros((128, 128), dtype=np.float32)

        one_hot = torch.zeros_like(logits)
        one_hot[0, target_class] = 1.0
        logits.backward(gradient=one_hot)

        grad = patch.grad.detach().cpu().squeeze().numpy()
        grad = np.maximum(grad, 0)
        if grad.max() > 0:
            grad = grad / grad.max()
        return grad

    def remove_hooks(self):
        for h in self.hooks:
            h.remove()

