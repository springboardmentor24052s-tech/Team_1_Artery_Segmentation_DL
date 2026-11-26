# Milestone 2 Technical Progress Report: Artery Segmentation, Morphological Processing and Caliber Analysis

**Internship Program:** Infosys Springboard Virtual Internship 7.0  
**Project Track & Domain:** Healthcare AI / Medical Image Analysis & Computer Vision (Artificial Intelligence)  
**Project Name:** Artery Segmentation and Stenosis Detection using Advanced Deep Learning Techniques  
**Application Name:** StenoVision  
**Group & Team:** Group-2, Team-1  
**Development & Execution Platform:** NVIDIA GeForce RTX 2050 (4.0 GB VRAM, CUDA 12.8) / PyTorch 2.1.0 [Required: 16 GB RAM, 20 GB Storage]  
**Milestone Status:** Completed and Evaluated (November 2026)  

---

## 1. Scope, Clinical Problem Statement and Objectives

### 1.1 Clinical Background and Problem Statement
Coronary artery disease remains a leading cause of cardiovascular mortality worldwide. During diagnostic cardiac catheterization, interventional cardiologists inject radiopaque contrast dye into the coronary circulation under live X-ray fluoroscopy. The resulting 2D X-ray Coronary Angiography (XCA) video frames display blood vessels as dark, branching structures against surrounding cardiac and thoracic tissue. In clinical practice, manual visual estimation of luminal narrowing is affected by cardiac motion, overlapping vessels, and catheter shadows, leading to reported inter-observer variability of up to 20%. To address this challenge, we developed an automated coronary artery segmentation and caliber quantification pipeline to provide an objective anatomical map of the vessel tree for downstream stenosis assessment.

### 1.2 Milestone Objectives and Curriculum Task Scorecard

| Task # and Module | Curriculum Objective | Engineered Code File | Delivered Component / Status |
|---|---|---|---|
| **Task 1: Baseline Architecture** | Construct standard symmetric segmentation network | `segmentation/models/unet.py` | We delivered the 4-level U-Net (~1.94M params, 37.6 FPS) |
| **Task 2: Attention Architecture** | Integrate spatial attention gates on skip connections | `segmentation/models/attention_unet.py` | We delivered Attention U-Net (~1.96M params, 33.9 FPS) |
| **Task 3: GPU Training Engine** | Train on GPU with mixed precision and Dice-BCE loss | `segmentation/training/train.py` | We trained both models on RTX 2050 (40 epochs, Val Dice: 0.7354) |
| **Task 4: Mask Ingestion** | Rasterize polygon ground truth into binary masks | `segmentation/training/dataset.py` | We rasterized 1,500 ARCADE masks (1000 train / 200 val / 300 test) |
| **Task 5: Post-Processing** | Filter catheter noise and seal small lumen breaks | `segmentation/postprocessing/cleaner.py` | We engineered a 4-stage post-processing pipeline |
| **Task 6: Vessel Structure** | Extract multi-scale vascular boundaries | `segmentation/analysis/centerline.py` | We extracted contours and branch points |
| **Task 7: Centerline Thinning** | Extract 1-pixel medial topological skeleton | `segmentation/analysis/centerline.py` | We computed centerlines with Zhang-Suen thinning |
| **Task 8: Caliper Profiling** | Calculate orthogonal lumen diameters in mm | `segmentation/analysis/diameter.py` | We calculated calibers via distance transform (0.25 mm/px) |
| **Task 9: Model Benchmarking** | Evaluate both models on 300 held-out test images | `segmentation/evaluation/evaluate.py` | We benchmarked on 300 test images (DSC, IoU, Recall, FPS) |
| **Task 10: Standalone Runner** | Build inference CLI and qualitative plotting tool | `milestone_2_results/predict.py` | We delivered standalone CLI runner and visual figures |

### 1.3 End-to-End Processing Workflow
We structured our processing pipeline into four sequential stages: (1) we applied Contrast-Limited Adaptive Histogram Equalization (CLAHE) to enhance contrast along faint vessel contours; (2) we executed semantic segmentation using Attention U-Net and baseline U-Net to generate binary vessel lumen masks; (3) we applied morphological post-processing (closing, component filtering, and hole filling) to clean isolated noise and seal minor breaks; and (4) we extracted medial centerlines via Zhang-Suen thinning and measured vessel calibers using the Euclidean Distance Transform (EDT).

### 1.4 Preprocessing Pipeline and Ground-Truth Rasterization
To prepare raw angiograms from the ARCADE challenge benchmark for deep learning training, we established a five-step preprocessing workflow: we rasterized polygon annotations into binary masks, paired images and masks using dataset manifests, verified native 512x512 resolution across all frames, applied CLAHE, and synthesized training batches with geometric augmentations:

| Step # | Operation | Implementation Details | Technical Purpose |
|---|---|---|---|
| **Step 1** | Polygon Rasterization | `cv2.fillPoly` parses polygon vertices from JSON annotations | We generated single-channel 512x512 binary ground-truth masks. |
| **Step 2** | Sample Pairing | Direct matching of image IDs in dataset manifests | We ensured every angiogram was strictly mapped to its verified mask. |
| **Step 3** | Dimensional Verification | Validates 512x512 native resolution across all frames | We confirmed uniform tensor dimensions without spatial distortion. |
| **Step 4** | Contrast Enhancement (CLAHE) | CLAHE with clip limit 2.0 and 8x8 tile grid, scaled to [0, 1] | We improved visibility of faint distal vessels without amplifying background noise. |
| **Step 5** | Data Augmentation and Batching | Random horizontal/vertical flips and small rotations (+/- 10 deg) | We improved model generalization across variable patient anatomies. |

---

## 2. Expected Outcomes and Delivered Results (Verification Matrix)

| Expected Technical Outcome | Delivered Component | Observed Metric / Benchmark | Verification Status |
|---|---|---|---|
| **Baseline Segmentation Architecture** | Canonical 4-Stage Symmetric U-Net | Dice: 0.6822, IoU: 0.5325, Throughput: 37.6 FPS | We verified via test set evaluation |
| **Attention Segmentation Architecture** | Spatial Attention Gates Attention U-Net | Dice: 0.6833, IoU: 0.5356, Throughput: 33.9 FPS | We verified via test set evaluation |
| **GPU Accelerated Training Engine** | Mixed Precision (AMP) + Dice-BCE Loss | RTX 2050 GPU, Cosine LR Decay, Val Dice: 0.7354 | We verified over 40 training epochs |
| **Ground-Truth Mask Ingestion** | cv2.fillPoly Rasterization (1,500 masks) | 1,000 Train / 200 Val / 300 Held-Out Test Split | We verified dataset manifest hashes |
| **Morphological Mask Post-Processing** | 4-Stage Cleanup (Close, Filter, Fill) | Removes noise <35px, seals breaks, preserves topology | We verified on post-processing pipeline |
| **Topological Centerline and Calipers** | Zhang-Suen Thinning + Distance Transform | Extracts 1-pixel skeleton, computes MLD and RVD in mm | We verified geometric measurements |

We verified that both models achieved approximately 0.68 Dice similarity on our held-out test split of 300 clinical angiograms, with high specificity (99.09%) and throughput exceeding 30 frames per second on our consumer laptop GPU (NVIDIA RTX 2050). We selected Attention U-Net as our default model for downstream tasks based on its qualitative reduction of catheter guide wire artifacts.

---

## 3. Technical Methodology and Architectural Design

### 3.1 Segmentation Architectures: Baseline U-Net and Attention U-Net
We constructed a baseline 4-level U-Net architecture with 16, 32, 64, and 128 channels, bridged by a 256-channel bottleneck. In baseline U-Net, standard skip connections transfer high-resolution spatial feature maps directly from encoder stages to matching decoder stages via concatenation. In angiograms, we observed that standard skip connections can also pass high-contrast non-vascular structures such as radiopaque catheter tips and rib edges. To address this, we implemented Attention U-Net, where we inserted Spatial Attention Gates into each skip connection.

In our Attention Gate implementation, we used the coarser feature map from the lower decoder stage as a gating signal $g$ to compute spatial attention coefficients $\alpha$. We passed the combined intermediate representation through a ReLU activation before final projection and sigmoid scaling:

$$\alpha = \sigma\left(\psi\left(\text{ReLU}\left(W_g * g + W_x * x\right)\right)\right)$$

where $x$ is the skip feature map, $W_g$ and $W_x$ are $1 \times 1$ convolutions with batch normalization, $\psi$ is a $1 \times 1$ convolution with batch normalization, and $\sigma$ is the sigmoid activation function. We computed the gated feature map through element-wise multiplication $\hat{x} = \alpha \cdot x$.

| Architectural Dimension | Baseline U-Net | Attention U-Net | Our Design Notes |
|---|---|---|---|
| **Encoder Depth** | 4 levels (16, 32, 64, 128 channels) | 4 levels (16, 32, 64, 128 channels) | We adapted the channel depth for our 4 GB GPU boundary |
| **Skip Connection Type** | Direct concatenation | Attention-Gated concatenation | We suppressed background activations along skip paths |
| **Bottleneck Channels** | 256 channels (32x32 spatial) | 256 channels (32x32 spatial) | We captured compact global context of the vascular tree |
| **Total Parameters** | 1,942,289 parameters | 1,964,657 parameters | We observed +1.1% parameters for spatial attention gates |
| **Checkpoint Size** | ~23.4 MB | ~23.7 MB | We retained a lightweight footprint for edge workstation deployment |
| **Inference Latency** | 26.6 ms per frame | 29.5 ms per frame | We measured on our NVIDIA RTX 2050 laptop GPU (FP16) |
| **Inference Throughput** | 37.6 FPS | 33.9 FPS | We confirmed both models exceeded standard video playback rates |

#### 3.1.1 Architectural Component Breakdown
We designed both networks with a symmetric 4-level structure for 512x512 single-channel inputs:
- **Encoder (Contracting Path):** We used four downsampling blocks. Each block applied two consecutive 3x3 convolutions with batch normalization and ReLU, followed by 2x2 max-pooling (stride 2). Channels doubled at each level: 16 -> 32 -> 64 -> 128.
- **Bottleneck Layer:** We operated at 32x32 resolution with 256 channels, capturing high-level contextual information across the entire coronary field.
- **Decoder (Expanding Path):** We constructed four upsampling blocks. Each block applied a 2x2 transposed convolution (halving channels), concatenated with the matching encoder feature map, and executed two 3x3 convolutions with ReLU.
- **Skip Connections:** We forwarded shallow spatial features to the decoder. Unlike additive residual shortcuts in ResNet, we used channel concatenation for U-Net skip connections. In Attention U-Net, our Attention Gate scaled the encoder features prior to concatenation.

### 3.2 Loss Function and Optimization Strategy
Because coronary arteries occupied fewer than 4% of total pixels in our angiograms, we found that training with binary cross-entropy (BCE) alone biased the model toward background predictions, since predicting all zeros achieved over 96% accuracy. To handle this class imbalance, we formulated and trained with a combined Dice-BCE loss:

$$\mathcal{L}_{total} = 0.5 \times \mathcal{L}_{BCE} + 1.0 \times \mathcal{L}_{Dice}$$

where $\mathcal{L}_{Dice} = 1 - \frac{2 \sum (p \cdot y) + \epsilon}{\sum p + \sum y + \epsilon}$. The Dice loss directly optimized the spatial overlap between predicted and ground-truth vessel masks, penalizing false negatives along thin arterial branches.

| Hyperparameter | Selected Value | Our Implementation Rationale |
|---|---|---|
| **Optimizer** | AdamW ($\beta_1=0.9, \beta_2=0.999$) | We used decoupled weight decay ($1 \times 10^{-2}$) to prevent overfitting on fine capillary structures |
| **Learning Rate Schedule** | $1 \times 10^{-4}$ initial, Cosine Annealing | We applied smooth learning rate reduction to avoid optimization divergence |
| **Batch Size and Epochs** | Batch Size: 8 \| Epochs: 40 | We configured batch size to maximize GPU memory utilization within 4.0 GB VRAM |
| **Mixed Precision (AMP)** | PyTorch `torch.cuda.amp` (FP16) | We reduced memory consumption and accelerated training using Tensor Cores |
| **Loss Weights** | $0.5 \times \text{BCE} + 1.0 \times \text{Dice}$ | We balanced individual pixel likelihoods with region-level overlap |
| **Hardware Engine** | NVIDIA GeForce RTX 2050 (4 GB) | We demonstrated feasibility on standard consumer laptop workstation hardware |

### 3.3 Morphological Post-Processing Pipeline
Because the raw model output was a continuous probability map $[0, 1]$, we engineered a 4-stage post-processing sequence to refine predictions into a clean mask:
1. **Stage 1 — Thresholding:** We binarized continuous probabilities at $T=0.50$ based on validation set calibration.
2. **Stage 2 — Morphological Closing:** We applied a 3x3 elliptical structuring element to bridge minor 1-2 pixel discontinuities along thin distal branches.
3. **Stage 3 — Component Filtering:** We removed small disconnected foreground fragments smaller than 35 pixels, which typically originated from catheter guide wire tips.
4. **Stage 4 — Binary Hole Filling:** We filled internal pinhole voids within proximal vessel lumens caused by non-uniform contrast filling.

#### 3.3.1 Post-Processing Operations and Considerations

| Operation | Target Artifact | Selected Parameter | Our Tuning Consideration |
|---|---|---|---|
| **Threshold Binarization** | Continuous probabilities [0, 1] | Fixed $T = 0.50$ | We found thresholds >0.6 pruned thin vessels, while <0.4 increased boundary false positives. |
| **Morphological Closing** | Micro-breaks in thin vessels | 3x3 elliptical kernel | We restricted kernel size to 3x3 because larger kernels (>5x5) risked bridging true tight stenotic gaps. |
| **Component Filtering** | Isolated catheter and wire tips | Area threshold = 35 pixels | We set the cutoff at 35 pixels because thresholds above 50 risked removing genuine detached distal capillaries. |
| **Binary Hole Filling** | Internal lumen voids | Homotopic 8-connected fill | We restored solid vessel cores by applying hole filling strictly to fully enclosed internal voids. |

### 3.4 Centerline Thinning and Caliber Quantification
We implemented the Zhang-Suen iterative thinning algorithm to extract vessel centerlines, reducing the binary mask to a 1-pixel-wide skeleton while strictly preserving 8-connectivity and branch topology. At every skeleton coordinate $(x, y)$, we applied the Euclidean Distance Transform (EDT) to compute the radius $r(x, y)$ to the nearest vessel boundary. In the absence of DICOM header pixel spacing metadata or explicit catheter calibration markers, we applied a standard assumed nominal scale of $0.25\text{ mm/pixel}$ (typical for standard catheterization fields of view):

$$\text{Diameter}(x, y) = 2 \times r(x, y) \times 0.25\text{ mm/px}$$

**Worked Example:** In our evaluation of a proximal Left Anterior Descending (LAD) segment:
1. **Reference Vessel Diameter (RVD):** We took the 75th percentile of the normal segment diameter array to establish an EDT radius of 6.4 pixels:
   $$\text{RVD} = 2 \times 6.4\text{ px} \times 0.25\text{ mm/px} = 3.20\text{ mm}$$
2. **Minimum Lumen Diameter (MLD):** We took the 5th percentile of the constriction segment profile (filtering single-pixel skeleton erosion noise) to measure an EDT radius of 1.92 pixels:
   $$\text{MLD} = 2 \times 1.92\text{ px} \times 0.25\text{ mm/px} = 0.96\text{ mm}$$
3. **Percent Diameter Stenosis (%DS):** We calculated %DS:
   $$\%DS = \left(1 - \frac{\text{MLD}}{\text{RVD}}\right) \times 100\% = \left(1 - \frac{0.96}{3.20}\right) \times 100\% = 70.0\%$$
Under ACC/AHA guidelines, this 70.0% narrowing represented severe stenosis, indicating hemodynamic significance.

#### 3.4.1 Centerline Key Point Classification

| Key Point Type | Neighbor Condition | Anatomical Interpretation | Our Analytical Role |
|---|---|---|---|
| **End Point** | Exactly 1 neighbor in 3x3 window | Terminal tip of distal branch or entry point | We used end points to define boundaries of individual arterial segments. |
| **Branch Point** | 3 or more neighbors in 3x3 window | Vascular bifurcation (e.g. LMCA dividing into LAD/LCx) | We partitioned the skeleton graph at branch points to prevent junction distortion. |
| **Vessel Segment** | Exactly 2 neighbors in 3x3 window | Continuous vessel section between key points | We utilized vessel segments as the local unit for caliber profiling. |

#### 3.4.2 Vessel Caliber Statistical Measures

| Statistical Measure | Definition | Clinical / Technical Role | Observed Range in Our Data |
|---|---|---|---|
| **Mean Diameter** | Mean of $D_i$ along segment | Characterizes average caliber of segment | 1.50 mm - 4.20 mm across major branches |
| **Median Diameter** | 50th percentile of $D_i$ array | Outlier-resistant baseline caliber | Robust against local calcification glare |
| **Minimum Lumen Diameter (MLD)** | 5th percentile of $D_i$ array | Isolates maximum constriction while filtering 1-px noise | <1.50 mm in significant lesions |
| **Reference Vessel Diameter (RVD)** | 75th percentile of healthy segment | Represents native un-diseased vessel caliber | 2.50 mm - 3.80 mm across normal segments |
| **Standard Deviation** | Std dev of $D_i$ along segment | Measures caliber uniformity along vessel path | Higher in irregular, ectatic, or diseased segments |

---

## 4. Quantitative Benchmark Results and Model Registry

### 4.1 Benchmark Evaluation on 300 Test Angiograms
We evaluated both segmentation architectures on 300 held-out clinical test angiograms from the ARCADE benchmark:

| Evaluation Metric | Baseline U-Net | Attention U-Net | Our Observed Difference |
|---|---|---|---|
| **Dice Similarity Coeff (DSC)** | 0.6822 +/- 0.1352 | 0.6833 +/- 0.1435 | +0.0011 (within std dev) |
| **Intersection over Union (IoU)** | 0.5325 +/- 0.1467 | 0.5356 +/- 0.1544 | +0.0031 |
| **Precision (PPV)** | 0.7325 | 0.7340 | +0.0015 |
| **Recall / Sensitivity (TPR)** | 0.6614 | 0.6642 | +0.0028 |
| **Specificity (TNR)** | 0.9905 | 0.9909 | +0.0004 |
| **Inference Latency (per frame)** | 26.61 ms | 29.46 ms | +2.85 ms |
| **Inference Throughput (FPS)** | 37.6 FPS | 33.9 FPS | -3.7 FPS |

**Our Analysis of Benchmark Results:**
1. **Global Overlap:** We observed that both models performed essentially identically on Dice score (~0.68), with the +0.0011 difference falling well within the $\pm 0.14$ standard deviation. Attention U-Net was slightly slower (33.9 vs 37.6 FPS) due to attention gate computations, but we chose it for downstream integration because our visual reviews showed that spatial attention gates qualitatively reduced spurious responses along high-contrast catheter guide wires.
2. **Sensitivity vs Specificity:** We found that recall (0.6642) reflected the challenge of segmenting faint, narrow distal capillary branches. Specificity was high (99.09%), which was expected given that background non-vascular tissue constituted over 96% of pixels.
3. **Computational Efficiency:** We confirmed that both models ran above 30 FPS on our laptop RTX 2050 GPU, demonstrating that real-time video playback rates (15 to 30 FPS) could be handled without specialized enterprise accelerators.

### 4.2 Model Checkpoint Registry

| Checkpoint File | Architecture | Parameters | Validation Metric | SHA-256 Hash |
|---|---|---|---|---|
| `best_attention_unet.pth` | Attention U-Net | 1,964,657 | Val Dice: 0.7354 | `cddb87821c60139836b4ebc1c7255d90fa8d985a5ab5b75d4ca1c7bdf5d64ec1` |
| `best_unet.pth` | Baseline U-Net | 1,942,289 | Val Dice: 0.7347 | `f21e4488049d924a2f9fb9e4331e43ac09dbb5f24df2c9afdba94a30774417d6` |
| `best_attention_unet_traced.pt` | Attention U-Net JIT | 1,964,657 | TorchScript Traced | `0342371373fa7eadc0f8ab1e5d9a5e5251e94bbbf04353f92fe7028066446980` |

---

## 5. Operational Clinical Workstation and Visual Evaluation

### 5.1 Web Application Interface and Diagnostic Workflows
We integrated our segmentation pipeline into a Next.js 15 clinical web application. We built interactive tools allowing clinicians to toggle raw angiogram frames, predicted segmentation masks, medial centerlines, and caliber readouts.

### 5.2 Qualitative Analysis of Benchmark Cases
We evaluated qualitative performance using 5-panel figures comparing the raw angiogram, expert manual ground-truth mask, baseline U-Net prediction, Attention U-Net prediction, and the extracted centerline with caliber overlay:

---

## 6. Technical Challenges and Failure Analysis

### 6.1 Engineering Challenges and Our Solutions
During the development of Milestone 2, our team encountered and addressed several practical engineering challenges:
1. **Vascular Sparsity:** When vessel lumen pixels occupied under 4% of total image area, standard binary cross-entropy resulted in slow convergence and favored background predictions. We combined Dice loss with BCE to force gradient updates based on spatial overlap, achieving stable convergence within 40 epochs.
2. **Extravascular Clutter:** When radio-opaque guide wires and dense bone structures produced false-positive responses in baseline U-Net skip connections, we introduced spatial attention gates to reduce these activations prior to concatenation, and we applied post-processing component filtering (<35 px) to prune remaining isolated speckles.
3. **Distal Vessel Breakage:** When binarizing sigmoid probabilities at T=0.50 produced occasional 1-2 pixel gaps along thin distal branches, we applied morphological closing with a 3x3 elliptical structuring element to seal these gaps and restore skeleton connectivity.
4. **Hardware Constraints:** When training 512x512 batches on our 4.0 GB laptop GPU caused out-of-memory errors, we adopted PyTorch Automatic Mixed Precision (AMP FP16), which reduced memory usage by approximately 45% and enabled stable batch sizes of 8.

### 6.2 Limitations and Failure Analysis
In evaluating our Milestone 2 results, we identified several important technical limitations:
1. **2D Projection Foreshortening:** We recognized that in single-plane fluoroscopy, 3D tortuous vessels are projected onto a 2D detector plate, causing segments running parallel to the beam to appear foreshortened and overlapping branches to merge. We identified multi-view biplane 3D reconstruction as an important future research direction.
2. **Boundary Discretization Limits:** We observed that at 512x512 resolution and an assumed 0.25 mm/pixel scale, a 1-pixel boundary uncertainty corresponds to 0.25 mm. In a small 1.0 mm distal vessel (4 pixels wide), a single-pixel error altered the calculated diameter by 25%. Consequently, we noted that caliber measurements on distal micro-vessels carry higher relative uncertainty than measurements on main proximal trunks (3.0 to 4.0 mm).
3. **Sensitivity on Distal Branches:** Our test recall of 0.6642 indicated that approximately one-third of fine capillary pixels were missed, occurring primarily in low-contrast peripheral branches where contrast agent diluted rapidly during cardiac cycles.
4. **Scale Calibration Assumption:** We applied an assumed nominal scale of 0.25 mm/pixel. While standard for cardiac catheterization fields of view, we noted that clinical deployment would require extracting exact pixel spacing from DICOM metadata or interactive catheter calibration markers.

---

## 7. Future Roadmap — 3D Modeling and System Extensions

### 7.1 Multi-View Biplane 3D Centerline Reconstruction
Because single-plane 2D angiography cannot resolve out-of-plane vessel curvature or true 3D spatial length, we outlined future work in epipolar geometry to fuse two simultaneous orthogonal projections (e.g. LAO and RAO views) to reconstruct 3D centerline spatial curves, eliminating foreshortening errors.

### 7.2 Preoperative CCTA Volume Co-Registration
We also investigated co-registering preoperative 3D Coronary Computed Tomography Angiography (CCTA) volumetric scans with live 2D fluoroscopy frames to provide catheterization guidance, particularly during complex chronic total occlusion procedures.

---

## 8. Conclusion, Deliverables Inventory and Transition Plan

### 8.1 Milestone Summary
In Milestone 2, our team established the core artery segmentation and vessel analysis pipeline for StenoVision. We trained and evaluated both U-Net and Attention U-Net architectures across 300 test angiograms, achieving ~0.68 Dice similarity, 99.09% specificity, and throughput exceeding 30 FPS on our laptop GPU. We implemented morphological post-processing, Zhang-Suen thinning, and Euclidean Distance Transform caliper profiling to extract centerline geometry and lumen diameters.

### 8.2 Deliverables Inventory

| Deliverable Category | File Path | Status / Verification |
|---|---|---|
| **Model Checkpoint** | `milestone_2_results/models/best_attention_unet.pth` | 23.7 MB, SHA-256 `cddb8782...` |
| **Model Checkpoint** | `milestone_2_results/models/best_unet.pth` | 23.4 MB, SHA-256 `f21e4488...` |
| **Traced Model** | `milestone_2_results/models/best_attention_unet_traced.pt` | 8.1 MB, SHA-256 `03423713...` |
| **Test Benchmark Metrics** | `milestone_2_results/metrics/comparison_results.json` | Attention U-Net: DSC 68.33%, IoU 53.56%, 33.9 FPS |
| **Qualitative Figures** | `milestone_2_results/qualitative_plots/test_case_*.png` | 5 high-resolution 5-panel figures |

### 8.3 Next Phase Transition Plan: Milestone 3
With artery segmentation, centerline thinning, and caliber quantification established, our team transitioned to Milestone 3: Stenosis Detection, Severity Classification, and Explainable AI. Our Attention U-Net masks and centerline caliber troughs provided the candidate search space for training Faster R-CNN and Multi-Task ResNet-18 diagnostic heads, subsequently feeding downstream automated clinical PDF, JSON, and CSV reporting and clinician digital sign-off workflows.

### 8.4 Technical Reference Notes
Core executable scripts delivered under Milestone 2:
- **`segmentation/analysis/diameter.py`:** Performs Zhang-Suen thinning, branch point classification, distance transform radius calculation, and millimeter caliber profiling.
- **`segmentation/evaluation/evaluate.py`:** Evaluates trained models across 300 test angiograms, computing Dice, IoU, Precision, Recall, Specificity, and inference latency.
- **`milestone_2_results/predict.py`:** Standalone inference script running CLAHE preprocessing, model segmentation, post-processing cleanup, and visual plot generation.
