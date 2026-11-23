# StenoVision Multi-Modality Cardiovascular Dataset Repository
**Infosys Springboard Virtual Internship 7.0 | Healthcare AI Track**  
**Lead AI Developer:** Sathiyamoorthi K | **Platform:** StenoVision v2.1  

---

## 1. Executive Summary

This directory (`StenoVision/data/`) houses the organized, validated, and standardized medical imaging datasets used for deep learning training, validation, and benchmarking in the StenoVision cardiovascular decision-support system.

To reflect authentic clinical practice, StenoVision integrates **dual imaging modalities**:
1. **2D X-Ray Coronary Angiography (XCA):** Real-time dynamic fluoroscopy recorded in catheterization suites during invasive Percutaneous Coronary Intervention (PCI).
2. **3D Computed Tomography Angiography (CCTA/CTPA):** High-resolution multi-detector helical volumetric CT scans used for non-invasive outpatient diagnostic triage.

```
====================================================================================================
MODALITY COMPARATIVE SUMMARY
====================================================================================================
Modality            | Physics & Dim          | Resolution       | Clinical Role         | Partitions
--------------------+------------------------+------------------+-----------------------+-----------
2D XCA Fluoroscopy  | 2D Dynamic X-ray       | 512 x 512 px     | Real-time PCI Guidance| 1,000 Train
                    | (8-bit grayscale)      | (0.2-0.3 mm/px)  | in Catheterization Lab|   200 Val
                    |                        |                  |                       |   300 Test
--------------------+------------------------+------------------+-----------------------+-----------
3D CCTA Volumetric  | 3D Helical CT Volume   | 512 x 512 x Z    | Non-invasive Triage,  |    70 Train
                    | (16-bit signed NIfTI)  | (0.65-0.78 mm xy)| Calcium Scoring,      |    15 Val
                    | [-1024, +3071] HU      | (1.0 mm slice)   | Surgical Roadmapping  |    15 Test
====================================================================================================
```

---

## 2. Directory Hierarchy

```text
StenoVision/data/
├── DATASET_CATALOG.json                # Master unified machine-readable multi-modality catalog
├── README.md                           # This comprehensive clinical documentation & guide
│
├── stenosis/                           # 2D ARCADE Task 1: Atherosclerotic Plaque Detection
│   ├── train/                          # 1,000 Angiograms (1,625 expert-annotated plaques)
│   │   ├── annotations/train.json      # MS-COCO format bounding boxes & polygon contours
│   │   └── images/*.png                # Standardized 512 x 512 8-bit grayscale projections
│   ├── val/                            # 200 Angiograms (406 plaques)
│   │   ├── annotations/val.json
│   │   └── images/*.png
│   └── test/                           # 300 Angiograms (386 held-out test plaques)
│       ├── annotations/test.json
│       └── images/*.png
│
├── syntax/                             # 2D ARCADE Task 2: 25-Class Anatomical Artery Segmentation
│   ├── train/                          # 1,000 Angiograms (4,976 artery segments)
│   │   ├── annotations/train.json      # 25 AHA/SYNTAX coronary branch classes
│   │   └── images/*.png
│   ├── val/                            # 200 Angiograms (1,168 artery segments)
│   │   ├── annotations/val.json
│   │   └── images/*.png
│   └── test/                           # 300 Angiograms (1,672 artery segments)
│       ├── annotations/test.json
│       └── images/*.png
│
├── masks/                              # Pre-Rasterized Binary Vessel Prior Masks (Lumen vs Background)
│   ├── train/*.png                     # 1,000 single-channel masks (0=background, 255=lumen)
│   ├── val/*.png                       # 200 single-channel masks
│   ├── test/*.png                      # 300 single-channel masks
│   ├── train_manifest.json             # Image-mask pair manifest with vessel pixel ratios
│   ├── val_manifest.json
│   └── test_manifest.json
│
└── 3d_ccta/                            # 3D Computed Tomography Angiography (Volumetric CT)
    ├── train/                          # 70 Patient Cases (20,571 total axial slices)
    │   └── PA0000XX/
    │       ├── image/PA0000XX.nii.gz   # Primary contrast-enhanced 3D CCTA volume
    │       └── label/PA0000XX.nii.gz   # 3D ground-truth vascular lumen segmentation
    ├── val/                            # 15 Patient Cases (4,627 total axial slices)
    │   └── PA0000XX/
    │       ├── image/PA0000XX.nii.gz
    │       └── label/PA0000XX.nii.gz
    ├── test/                           # 15 Held-out Patient Cases (5,142 total axial slices)
    │   └── PA0000XX/
    │       ├── image/PA0000XX.nii.gz
    │       └── label/PA0000XX.nii.gz
    ├── train_manifest.json             # 70 Volume records (shapes, slice count, HU range)
    ├── val_manifest.json               # 15 Volume records
    ├── test_manifest.json              # 15 Volume records
    └── dataset_summary.json            # Aggregate volume statistics & density distributions
```

---

## 3. 2D X-Ray Angiography Dataset (MICCAI ARCADE)

### 3.1 Overview
The ARCADE dataset is the interventional cardiology gold standard curated for the MICCAI 2023 challenge. It comprises $1,500$ clinical angiographic frames recorded from patients aged 19 to 90 years on Philips Azurion 3 and Siemens Artis Zee systems. Ground truth was established by board-certified interventional cardiologists using CVAT.

### 3.2 Partition Breakdown
| Partition | Purpose | Image Count | Stenosis Plaques | Artery Polygons | Rasterized Masks |
|---|---|---:|---:|---:|---:|
| **Train** | Deep learning feature learning | 1,000 | 1,625 | 4,976 | 1,000 |
| **Val** | Validation & early stopping | 200 | 406 | 1,168 | 200 |
| **Test** | Held-out benchmark evaluation | 300 | 386 | 1,672 | 300 |
| **Total** | Full Benchmark Repository | **1,500** | **2,417** | **7,816** | **1,500** |

---

## 4. 3D Volumetric CCTA Dataset (PARSE Benchmark)

### 4.1 Overview
The 3D volumetric dataset comprises $100$ patient acquisitions with genuine dual contrast-enhanced CT angiography volumes and companion 3D ground-truth vascular tree masks. 

### 4.2 Partition Breakdown
* **Training Partition (`3d_ccta/train/`):** $70$ patient cases ($20,571$ axial slices, mean $293.9$ slices/patient).
* **Validation Partition (`3d_ccta/val/`):** $15$ patient cases ($4,627$ axial slices, mean $308.5$ slices/patient).
* **Testing Partition (`3d_ccta/test/`):** $15$ patient cases ($5,142$ axial slices, mean $342.8$ slices/patient).
* **Total Volume Matrix:** $512 \times 512 \times Z$ with $30,340$ total slices.

### 4.3 Recommended Clinical CT Windowing
Coronary vessels opacified with iodinated contrast typically inhabit the $[80, 550]\text{ HU}$ range. For deep learning input, voxel intensities are windowed using:
$$\text{Voxel}_{\text{norm}} = \text{clip}\left(\frac{\text{HU} - (-100)}{700}, 0.0, 1.0\right)$$

---

## 5. PyTorch Dataset Loading Quickstart

### 5.1 Loading 2D Artery Segmentation Data
```python
from StenoVision.segmentation.training.dataset import ArterySegmentationDataset

# Load 2D training dataset with CLAHE intensity normalization and augmentation
train_ds = ArterySegmentationDataset(
    manifest_path="StenoVision/data/masks/train_manifest.json",
    target_size=(512, 512),
    augment=True,
    use_clahe=True,
)
image_tensor, mask_tensor = train_ds[0]
print(f"2D Image Shape: {image_tensor.shape}, Mask Shape: {mask_tensor.shape}")
```

### 5.2 Loading 2D Stenosis Detection Data (Faster R-CNN)
```python
from StenoVision.stenosis.data_prep.dataset_coco import CoronaryStenosisDataset

# Load 2D test split for plaque detection
test_ds = CoronaryStenosisDataset(
    data_root="StenoVision",
    split="test",
    img_size=512,
)
image_tensor, target_dict = test_ds[0]
print(f"Image Tensor: {image_tensor.shape}, Bounding Boxes: {target_dict['boxes'].shape}")
```

### 5.3 Loading 3D Volumetric CCTA Data
```python
from StenoVision.stenosis.data_prep.dataset_3d_volume import Coronary3DVolumeDataset

# Load 3D test split (returns volume tensor and companion 3D mask)
test_3d_ds = Coronary3DVolumeDataset(
    manifest_path="StenoVision/data/3d_ccta/test_manifest.json",
    return_mode="optimal_slice",  # Options: 'volume', 'slab', 'optimal_slice'
    window_hu=(-100.0, 600.0),
)
slice_img, slice_mask, meta = test_3d_ds[0]
print(f"Patient: {meta['patient_id']} | Slice Shape: {slice_img.shape} | Slices in Volume: {meta['total_slices']}")
```

---

## 6. Verification & Quality Assurance

To audit the entire multi-modality dataset hierarchy and verify 100% integrity of all files, run:
```powershell
python StenoVision/scripts/verify_datasets_organization.py
```
This utility automatically checks:
* 1,500 2D XCA angiogram images and MS-COCO annotations across train, val, and test splits.
* 1,500 pre-rasterized binary vessel prior masks.
* 100 3D volumetric `.nii.gz` volumes and companion masks across 70 train, 15 val, and 15 test directories.
* Validates header parsability, slice counts, and JSON manifest synchronization.
