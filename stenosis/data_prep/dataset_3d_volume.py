"""
StenoVision - PyTorch 3D CCTA Volumetric Dataset Loader
======================================================
Loads 3D Computed Tomography Angiography (CCTA/CTPA) volumes and companion
ground-truth 3D vascular segmentation masks from structured JSON manifests.

Supports three clinical return modes:
- 'optimal_slice': Extracts the high-contrast 2D axial slice with companion mask (ideal for 2D networks).
- 'volume': Returns the full 3D volumetric tensor [1, D, H, W] and mask tensor [1, D, H, W].
- 'slab': Returns a multi-slice 2.5D slab [C, H, W] centered at the vascular target.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import nibabel as nib
import numpy as np
import torch
from torch.utils.data import Dataset


class Coronary3DVolumeDataset(Dataset):
    """
    Standard PyTorch Dataset for 3D CCTA/CTPA volumes and companion 3D masks.
    """

    def __init__(
        self,
        manifest_path: Union[str, Path],
        return_mode: str = "optimal_slice",  # 'optimal_slice', 'volume', or 'slab'
        window_hu: Tuple[float, float] = (-100.0, 600.0),
        target_2d_size: Tuple[int, int] = (512, 512),
        slab_thickness: int = 3,
    ):
        super().__init__()
        self.manifest_path = Path(manifest_path).resolve()
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")

        self.data_root = self.manifest_path.parent.parent  # StenoVision/data

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self.records: List[Dict] = json.load(f)

        self.return_mode = return_mode
        self.window_hu = window_hu
        self.target_2d_size = target_2d_size
        self.slab_thickness = slab_thickness

    def __len__(self) -> int:
        return len(self.records)

    def _apply_windowing(self, raw_hu: np.ndarray) -> np.ndarray:
        """Applies clinical CT windowing and maps intensities to [0.0, 1.0]."""
        w_min, w_max = self.window_hu
        clipped = np.clip(raw_hu, w_min, w_max)
        norm = (clipped - w_min) / (w_max - w_min + 1e-8)
        return norm.astype(np.float32)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, Dict]:
        record = self.records[idx]
        img_rel = record["relative_image_path"]
        lbl_rel = record.get("relative_label_path")

        # Resolve full path from data root
        img_path = self.data_root / img_rel
        lbl_path = (self.data_root / lbl_rel) if lbl_rel else None

        if not img_path.exists():
            raise FileNotFoundError(f"3D Image file not found: {img_path}")

        nii_img = nib.load(str(img_path))
        vol_hu = nii_img.get_fdata()

        vol_lbl = None
        if lbl_path and lbl_path.exists():
            try:
                nii_lbl = nib.load(str(lbl_path))
                vol_lbl = nii_lbl.get_fdata()
            except Exception:
                vol_lbl = np.zeros_like(vol_hu)
        else:
            vol_lbl = np.zeros_like(vol_hu)

        sel_slice = record.get("selected_slice_idx", vol_hu.shape[2] // 2)
        total_slices = vol_hu.shape[2]

        if self.return_mode == "optimal_slice":
            # Extract 2D slice
            slice_hu = vol_hu[:, :, sel_slice]
            slice_norm = self._apply_windowing(slice_hu)
            slice_gray = (slice_norm * 255.0).astype(np.uint8)
            slice_gray = cv2.rotate(slice_gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
            if slice_gray.shape != self.target_2d_size:
                slice_gray = cv2.resize(slice_gray, self.target_2d_size, interpolation=cv2.INTER_LINEAR)

            mask_slice = (vol_lbl[:, :, sel_slice] > 0).astype(np.uint8) * 255
            mask_slice = cv2.rotate(mask_slice, cv2.ROTATE_90_COUNTERCLOCKWISE)
            if mask_slice.shape != self.target_2d_size:
                mask_slice = cv2.resize(mask_slice, self.target_2d_size, interpolation=cv2.INTER_NEAREST)

            img_tensor = torch.from_numpy(slice_gray).float().unsqueeze(0) / 255.0  # [1, H, W]
            mask_tensor = torch.from_numpy(mask_slice).float().unsqueeze(0) / 255.0  # [1, H, W]

        elif self.return_mode == "slab":
            # Extract 2.5D slab around target slice
            half = self.slab_thickness // 2
            indices = [np.clip(sel_slice + i, 0, total_slices - 1) for i in range(-half, half + 1)]
            channels = []
            for s_idx in indices:
                s_hu = vol_hu[:, :, s_idx]
                s_norm = self._apply_windowing(s_hu)
                s_gray = (s_norm * 255.0).astype(np.uint8)
                s_gray = cv2.rotate(s_gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
                if s_gray.shape != self.target_2d_size:
                    s_gray = cv2.resize(s_gray, self.target_2d_size, interpolation=cv2.INTER_LINEAR)
                channels.append(s_gray)

            slab_np = np.stack(channels, axis=0)  # [C, H, W]
            mask_slice = (vol_lbl[:, :, sel_slice] > 0).astype(np.uint8) * 255
            mask_slice = cv2.rotate(mask_slice, cv2.ROTATE_90_COUNTERCLOCKWISE)
            if mask_slice.shape != self.target_2d_size:
                mask_slice = cv2.resize(mask_slice, self.target_2d_size, interpolation=cv2.INTER_NEAREST)

            img_tensor = torch.from_numpy(slab_np).float() / 255.0
            mask_tensor = torch.from_numpy(mask_slice).float().unsqueeze(0) / 255.0

        else:
            # Full 3D Volume tensor: [1, D, H, W]
            vol_norm = self._apply_windowing(vol_hu)
            vol_transposed = np.transpose(vol_norm, (2, 0, 1))  # [D, H, W]
            lbl_transposed = np.transpose((vol_lbl > 0).astype(np.float32), (2, 0, 1))

            img_tensor = torch.from_numpy(vol_transposed).float().unsqueeze(0)
            mask_tensor = torch.from_numpy(lbl_transposed).float().unsqueeze(0)

        metadata = {
            "patient_id": record["patient_id"],
            "split": record["split"],
            "total_slices": total_slices,
            "selected_slice": sel_slice,
            "voxel_spacing_mm": record.get("voxel_spacing_mm"),
            "volume_shape": record["volume_shape"],
            "return_mode": self.return_mode,
        }

        return img_tensor, mask_tensor, metadata
