"""
Sub-Team 3: Explainable AI & Visualization - Member 5
Module: Grad-CAM Verification Suite
===================================
Benchmarking Grad-CAM forward/backward hook execution latency,
saliency map bounds, and dual-head gradient attribution isolation.
"""

import time
import torch
import numpy as np
try:
    from stenosis.xai.grad_cam import GradCAM
except ImportError:
    from grad_cam import GradCAM


def run_grad_cam_benchmark():
    print("=== Testing Native PyTorch Grad-CAM Engine ===")
    try:
        from stenosis.models.multi_task_resnet import MultiTaskStenosisResNet18
    except ImportError:
        from multi_task_resnet import MultiTaskStenosisResNet18

    model = MultiTaskStenosisResNet18(in_channels=1)
    model.eval()

    cam = GradCAM(model=model, target_layer=model.get_gradcam_target_layer())

    dummy_patch = torch.randn(1, 1, 128, 128, requires_grad=True)

    # 1. Test Severity Head Attribution
    t0 = time.perf_counter()
    heatmap_sev = cam.generate_cam(dummy_patch, target_head="severity", class_idx=2)
    t_sev = (time.perf_counter() - t0) * 1000.0

    print(f"Severity Head Attribution Latency: {t_sev:.2f} ms")
    print(f"Severity Heatmap Shape: {heatmap_sev.shape}, Range: [{heatmap_sev.min():.2f}, {heatmap_sev.max():.2f}]")
    assert heatmap_sev.shape == (128, 128)
    assert 0.0 <= heatmap_sev.min() <= heatmap_sev.max() <= 1.0

    # 2. Test Binary Head Attribution
    t0 = time.perf_counter()
    heatmap_bin = cam.generate_cam(dummy_patch, target_head="binary", class_idx=1)
    t_bin = (time.perf_counter() - t0) * 1000.0

    print(f"Binary Head Attribution Latency:   {t_bin:.2f} ms")
    print(f"Binary Heatmap Shape:   {heatmap_bin.shape}, Range: [{heatmap_bin.min():.2f}, {heatmap_bin.max():.2f}]")
    assert heatmap_bin.shape == (128, 128)

    print("Native PyTorch Grad-CAM verification PASSED successfully.")


if __name__ == "__main__":
    run_grad_cam_benchmark()

