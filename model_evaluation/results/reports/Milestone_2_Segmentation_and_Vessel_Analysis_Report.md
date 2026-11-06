# Milestone 2 Technical Progress Report: Artery Segmentation, Morphological Post-Processing, and Vessel Analysis

**Internship:** Infosys Springboard Virtual Internship 7.0  
**Project Track:** Healthcare AI / Medical Image Analysis  
**Project Title:** Artery Segmentation and Stenosis Detection Using Advanced Deep Learning Techniques (StenoVision)  
**Author:** Sathiyamoorthi K | Milestone 2 Core Deliverable | November 2026  

---

## 1. Executive Summary and Milestone Objectives

This progress report details the engineering activities, machine learning methodologies, and experimental findings completed during Milestone 2 (Weeks 3 & 4) of the Infosys Springboard Virtual Internship 7.0. The primary focus of Milestone 2 is the research, development, training, post-processing, and evaluation of deep learning architectures for pixel-level coronary artery segmentation, coupled with advanced morphological vessel structure analysis on 2D X-Ray Coronary Angiography (XCA) images.

### Milestone 2 Tasks Scorecard (10 / 10 Completed)
1. **Baseline Segmentation Model:** Implemented standard 4-level encoder-decoder U-Net with skip connections (~1.94M parameters).
2. **Advanced Segmentation Model:** Implemented Attention U-Net incorporating spatial Attention Gates (AGs) on skip connections (~1.96M parameters).
3. **Model Training Engine:** Trained both models on NVIDIA GeForce RTX 2050 GPU using mixed precision (`torch.amp`) and Combined Dice-BCE loss.
4. **Artery Mask Generation:** Rasterized all 1,500 ARCADE SYNTAX polygon annotations into $512 \times 512$ ground-truth masks with split manifests.
5. **Segmentation Post-Processing:** Built thresholding ($T=0.50$), small connected component suppression ($<35$ px), morphological closing, and hole filling.
6. **Vessel Structure Extraction:** Extracted multi-scale vessel contour boundaries and structural attributes.
7. **Centerline Extraction:** Extracted 1-pixel medial skeletons via Zhang-Suen thinning and identified branch points and endpoints.
8. **Vessel Diameter Estimation:** Mapped local diameters via Euclidean Distance Transform to compute Reference Vessel Diameter (RVD) and Minimum Luminal Diameter (MLD).
9. **Model Comparison:** Benchmarked both models on 300 held-out test images across Dice, IoU, Precision, Recall, Specificity, and Latency.
10. **Performance Reporting:** Generated 5-panel clinical qualitative figures and comprehensive performance reports in Word and Markdown.

---

## 2. Deep Learning Segmentation Architectures

### 2.1 Baseline Architecture: U-Net
The baseline model implements the canonical symmetric U-Net architecture. The contracting encoder path consists of four resolution levels (16 -> 32 -> 64 -> 128 feature channels), each containing two $3 \times 3$ convolutions, batch normalization, and ReLU activations, followed by $2 \times 2$ max pooling. A 256-channel bottleneck bridges the encoder to a four-stage expanding decoder path with $2 \times 2$ transposed convolutions and direct skip concatenation.

### 2.2 Advanced Architecture: Attention U-Net
To overcome the limitation of standard skip connections transferring background clutter into the decoder, we implemented the Attention U-Net. Spatial Attention Gates (AGs) are inserted at each skip connection. The Attention Gate uses the coarse decoder feature map as a gating signal to compute spatial attention coefficients via additive projection:
$$\alpha = \sigma(\psi(W_g * g + W_x * x))$$
This dynamically highlights coronary vascular structures while attenuating background noise before skip concatenation.

#### Table 1: Model Architecture Comparison Matrix

| Architectural Feature | Baseline U-Net | Attention U-Net | Clinical / Technical Advantage |
|---|---|---|---|
| **Encoder Depth** | 4 levels (16-128 channels) | 4 levels (16-128 channels) | Lightweight footprint optimized for 4 GB GPU VRAM |
| **Skip Connection Type** | Direct concatenation | Attention-Gated concatenation | Suppresses radiopaque catheters & bone shadows |
| **Bottleneck Channels** | 256 channels | 256 channels | Compact semantic latent representation |
| **Total Parameters** | 1,942,289 parameters | 1,964,657 parameters | +1.1% parameters adds powerful spatial attention |
| **Memory Footprint** | ~7.4 MB weights | ~7.5 MB weights | Ultra-fast loading & edge deployment feasibility |
| **Inference Latency** | 26.6 ms (37.6 FPS) | 29.4 ms (33.9 FPS) | Both exceed real-time clinical threshold (>30 FPS) |

---

## 3. Training Methodology and Ground-Truth Rasterization

Ground truth polygon segmentations in the ARCADE SYNTAX benchmark were rasterized into $512 \times 512$ single-channel 8-bit binary masks using `cv2.fillPoly`. 1,000 training, 200 validation, and 300 test masks were generated and organized with JSON manifests.

To handle foreground sparsity, models were trained using a Combined Dice-BCE Loss:
$$\mathcal{L} = 0.5 \times \mathcal{L}_{BCE} + 1.0 \times \mathcal{L}_{Dice}$$
Training was executed on an NVIDIA GeForce RTX 2050 GPU utilizing mixed precision (`torch.amp.autocast`) and the AdamW optimizer (initial lr=1e-3, cosine decay to 1e-5). Validation Dice scores converged rapidly, reaching **0.7347** for U-Net and **0.7354** for Attention U-Net.

---

## 4. Segmentation Post-Processing Pipeline

Raw sigmoid logits from neural network inference were refined through a 4-stage post-processing pipeline:
1. **Probability Thresholding:** Sigmoid probabilities are thresholded at $T=0.50$ into a binary mask.
2. **Morphological Closing:** A $3 \times 3$ elliptical structuring element bridges micro-discontinuities in thin vessel branches.
3. **Topological Hole Filling:** Applies binary topological fill-holes to prevent artificial voids inside wide proximal lumens.
4. **Component Area Filtering:** Connected component labeling filters out all isolated false-positive fragments smaller than 35 pixels (e.g., catheter tip noise).

---

## 5. Vessel Structure, Centerline Extraction & Diameter Estimation

### 5.1 Zhang-Suen Morphological Thinning
Centerline extraction transforms 2D binary vessel masks into a 1-pixel wide topological medial axis using the Zhang-Suen iterative thinning algorithm (`cv2.ximgproc.thinning`). The algorithm guarantees 8-connectivity and preserves the vascular homotopy.

Topological feature analysis on the extracted skeleton evaluates the 8-connected neighborhood of each centerline pixel: pixels with degree = 1 represent vessel terminations (endpoints), degree = 2 represent continuous segments, and degree $\ge 3$ represent bifurcations or trifurcations (branch points).

### 5.2 Orthogonal Diameter Estimation via Distance Transform
Vessel diameter is estimated by applying the Euclidean Distance Transform (EDT) on the binary mask. At each centerline pixel $(x, y)$, the distance transform value $r(x, y)$ represents the orthogonal in-lumen radius. The local vessel diameter is:
$$\text{Diameter}(x, y) = 2 \times r(x, y)$$
Multiplying pixel diameters by the clinical in-plane spacing (~0.25 mm/px) yields physical measurements in millimeters:
- **Reference Vessel Diameter (RVD):** 75th percentile of normal non-diseased vessel segment diameters.
- **Minimum Luminal Diameter (MLD):** 5th percentile of luminal narrowing along the vessel tract (robust against boundary artifacts).
- **Percent Diameter Stenosis:**
  $$\text{Percent Stenosis} = \left(1 - \frac{\text{MLD}}{\text{RVD}}\right) \times 100\%$$

---

## 6. Comparative Experimental Results and Model Selection

Both models were rigorously benchmarked on the held-out test split of 300 unseen clinical angiograms.

#### Table 2: Test Split Benchmark Comparison (300 Images)

| Performance Metric | Baseline U-Net | Advanced Attention U-Net | Superiority / Delta |
|---|---|---|---|
| **Dice Similarity Coeff (DSC)** | 0.6822 $\pm$ 0.1352 | **0.6833 $\pm$ 0.1435** | **+0.11% (Winner)** |
| **Intersection over Union (IoU)** | 0.5325 $\pm$ 0.1467 | **0.5356 $\pm$ 0.1544** | **+0.31% (Winner)** |
| **Precision (PPV)** | 0.7325 | **0.7340** | **+0.15% (Winner)** |
| **Recall / Sensitivity (TPR)** | 0.6614 | **0.6642** | **+0.28% (Winner)** |
| **Specificity (TNR)** | 0.9905 | **0.9909** | **+0.04% (Winner)** |
| **Inference Latency (per frame)** | **26.61 ms** | 29.46 ms | +2.85 ms overhead |
| **Throughput (FPS)** | **37.6 FPS** | 33.9 FPS | Real-Time (>30 FPS) |

### 6.1 Model Selection Justification: Attention U-Net
Based on quantitative test set evaluation across all 300 test angiograms, **Attention U-Net is selected as the definitive segmentation engine for StenoVision**. Attention U-Net demonstrates superior Dice score (0.6833), higher IoU (0.5356), higher precision (0.7340), and higher sensitivity (0.6642). Furthermore, at 33.9 FPS (29.4 ms per frame), Attention U-Net easily surpasses the 30 FPS threshold required for real-time Cath Lab deployment.

### 6.2 Clinical Qualitative Visualizations
Five-panel clinical qualitative figures were generated across diverse test angiograms, comparing raw images, ground truth masks, U-Net predictions, Attention U-Net predictions, and vessel centerline diameter heatmaps. Inspection demonstrates that Attention U-Net successfully eliminates false-positive catheter shadows while maintaining continuity along distal branches.

---

## 7. Milestone 2 Overall Conclusion and Transition to Milestone 3

Milestone 2 has successfully established a high-performance, real-time artery segmentation and morphological analysis engine for StenoVision. All ten tasks and five expected outcomes are fully accomplished:
- **Engine Operational:** Deep learning segmentation architectures (U-Net and Attention U-Net) were implemented, trained on GPU, and evaluated on 300 test images.
- **Superior Model Selected:** Attention U-Net was selected as the superior architecture, achieving **0.6833 Dice score** and **33.9 FPS** real-time throughput.
- **Vessel Structure Analysis:** Morphological pipeline extracts 1-pixel centerlines, topological bifurcations, and physical diameters (RVD and MLD).
- **Robust Clinical Post-Processing:** Automated post-processing eliminates catheter clutter and isolates intact coronary trees.

With artery segmentation, centerline extraction, and diameter quantification operational, StenoVision is primed to advance to **Milestone 3: Stenosis Detection, Bounding Box Localization, and Plaque Severity Classification**.
