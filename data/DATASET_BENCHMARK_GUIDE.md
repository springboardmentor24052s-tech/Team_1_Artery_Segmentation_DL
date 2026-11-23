# Clinical Benchmark Datasets Guide

This folder contains verified benchmark datasets utilized for training, cross-validation, and independent clinical testing of the StenoVision coronary stenosis detection platform.

## Dataset Structure

```
07_Benchmark_Clinical_Datasets/
├── DATASET_CATALOG.json             # Exhaustive dataset catalog with provenance & hashes
├── README.md                        # Dataset documentation & technical specifications
├── 2d_xray_angiograms/
│   ├── images/                      # Benchmark 2D X-ray coronary angiograms (ARCADE 2023)
│   │   ├── 10.png
│   │   ├── 35.png
│   │   ├── 60.png
│   │   ├── 110.png
│   │   └── 175.png
│   └── ground_truth_masks/          # Expert cardiologist vessel & stenosis segmentations
│       ├── 10.png
│       ├── 35.png
│       ├── 60.png
│       ├── 110.png
│       └── 175.png
└── 3d_ccta_volumes/
    ├── dataset_summary.json         # Summary of 3D CTPA/CCTA pulmonary & coronary artery data
    ├── train_manifest.json          # 3D training split manifest (PARSE 2022)
    ├── val_manifest.json            # 3D validation split manifest
    ├── test_manifest.json           # 3D test split manifest
    └── sample_case_PA000296/        # Representative 3D NIfTI volume (image & binary mask)
        ├── image/PA000296.nii.gz
        └── label/PA000296.nii.gz
```

## Data Provenance & Modalities

1. **ARCADE 2023 (Artery Coronary Angiography and Detection Evaluation)**:
   - Primary 2D modality: X-ray Coronary Angiograms (XCA)
   - Resolution: 512x512
   - Annotation: Vessel binary masks, stenosis bounding boxes, severity classifications (<50% Mild, 50-70% Moderate, >70% Severe).
2. **PARSE 2022 (Pulmonary Artery Segmentation Challenge)**:
   - 3D Modality: Computed Tomography Pulmonary Angiography (CTPA) / CCTA volumes
   - Format: NIfTI 3D gzip (`.nii.gz`)
   - Preprocessing: HU windowing (-150 to +500 HU), 1.0mm isotropic resampling.
