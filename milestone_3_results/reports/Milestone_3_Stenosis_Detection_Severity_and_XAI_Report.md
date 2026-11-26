# Milestone 3 Technical Progress Report: Stenosis Detection, Severity Classification and Explainable AI

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
While in Milestone 2 our team focused on isolating the coronary arterial tree, in Milestone 3 we directed our efforts toward pathological diagnosis: detecting atherosclerotic lesions, quantifying percent diameter stenosis (%DS), grading lesion severity into ACC/AHA clinical tiers, and generating visual explainability maps. In cardiac catheterization, interventional cardiologists assess angiograms under tight time constraints to determine whether a lesion warrants revascularization. Because visual estimation of stenosis severity suffers from reported inter-observer variability of 8% to 12% in clinical literature, we developed a multi-stage deep learning pipeline to provide automated candidate detection, standardized severity grading, and Grad-CAM visual attention maps.

Across our complete diagnostic pipeline, we integrated three deep learning models:
1. We utilized our frozen Attention U-Net from Milestone 2 for full-frame arterial tree segmentation and centerline tracking;
2. We trained Faster R-CNN (MobileNetV3-Large FPN backbone) for candidate lesion bounding box localization; and
3. We engineered Multi-Task ResNet-18 to simultaneously predict lesion presence, ACC/AHA 4-tier severity grade, and %DS on localized 128x128 patches, paired with Grad-CAM explainability.

Each report includes patient demographics, coronary measurements, stenosis severity, clinical recommendations, and four-panel diagnostic visualizations. We also integrated PDF, JSON, and CSV export endpoints, along with radiologist/clinician digital sign-off and approval workflows.

### 1.2 Milestone Objectives and Curriculum Task Scorecard

| Task # and Module | Curriculum Objective | Engineered Code File | Delivered Component / Status |
|---|---|---|---|
| **Task 1: Faster R-CNN Detector** | Construct object detector for lesion bounding boxes | `stenosis/models/detector.py` | We delivered Faster R-CNN (MobileNetV3 FPN, 151.5 MB) |
| **Task 2: Multi-Task ResNet-18** | Build joint classifier and %DS regression network | `stenosis/models/multi_task_resnet.py` | We delivered Multi-Task ResNet-18 (3 heads, 138.2 MB) |
| **Task 3: GPU Training Engine** | Train detector and multi-task classifier on GPU | `stenosis/training/train_classifier.py` | We trained on RTX 2050 (40 epochs, Val Acc: 78.2%) |
| **Task 4: Lesion Localization** | Deduplicate candidate boxes and map branch labels | `stenosis/localization/branch_mapper.py` | We mapped lesions to LAD, LCx, and RCA branches |
| **Task 5: QCA Caliper Engine** | Compute MLD, RVD, %DS, and lesion length | `stenosis/severity/qca_calculator.py` | We calculated calibers calibrated at 0.25 mm/px scale |
| **Task 6: Severity Grading** | Map %DS to ACC/AHA 4-tier clinical categories | `stenosis/severity/severity_grader.py` | We implemented ACC/AHA grading (Mild, Mod, Sev, Occ) |
| **Task 7: Grad-CAM Explainability** | Generate activation heatmaps with vessel masking | `stenosis/xai/grad_cam.py` | We implemented lumen-masked Grad-CAM on layer4 |
| **Task 8: Benchmark Evaluation** | Benchmark on 300 test angiograms (386 lesions) | `stenosis/evaluation/evaluate_stenosis.py` | We evaluated test set (Acc: 74.86%, %DS MAE: 9.54%) |
| **Task 9: Diagnostic Pipeline** | Unified end-to-end CLI diagnostic runner | `stenosis/pipeline.py` | We delivered the integrated CLI and Python pipeline |

### 1.3 End-to-End Processing Workflow
We structured our diagnostic pipeline into four stages: (1) we performed full-frame artery segmentation and centerline extraction using our frozen Attention U-Net from Milestone 2; (2) we localized candidate lesions by combining Faster R-CNN proposals with centerline caliper narrowing troughs; (3) we evaluated 128x128 cropped candidate patches using Multi-Task ResNet-18 to determine lesion presence, ACC/AHA severity tier, and continuous %DS; and (4) we generated Grad-CAM visual attributions masked by our vessel segmentation to ensure heatmaps remained confined strictly to the arterial lumen.

---

## 2. Expected Outcomes and Delivered Results (Verification Matrix)

| Expected Technical Outcome | Delivered Component | Observed Metric / Benchmark | Verification Status |
|---|---|---|---|
| **Candidate Lesion Localization** | Faster R-CNN (MobileNetV3 FPN) | Inference Latency: 33.55 ms, FPS: 29.8 | We verified via test set evaluation |
| **Severity Classification Head** | Multi-Task ResNet-18 Classifier | Accuracy: 74.86% (4 ACC/AHA tiers) | We verified via test set evaluation |
| **Quantitative %DS Regression** | Multi-Task ResNet-18 Linear Head | Mean Absolute Error (MAE): 9.54% %DS | We verified via test set evaluation |
| **Branch Attribution Mapping** | Centroid-based spatial branch mapper | Categorizes into LAD, LCx, or RCA | We verified geometric branch mapping |
| **Explainable AI Heatmaps** | PyTorch Grad-CAM with lumen masking | Zero extravascular gradient leakage | We verified visual heatmap confinement |
| **End-to-End Diagnostic Pipeline** | Unified Python API and CLI runner | Multi-stage pipeline on CPU and GPU | We verified end-to-end execution |

---

## 3. Technical Methodology and Multi-Stage Architecture

### 3.1 Two-Stage Detection and Classification Pipeline
Because stenosis lesions occupied small localized regions (typically under 30x30 pixels), we found that evaluating stenosis directly on full 512x512 angiograms with a single classifier was computationally inefficient and diluted focal gradient signals. We developed a two-stage architecture: we first utilized Faster R-CNN as a candidate generator to scan the full frame for suspect regions, and we then evaluated cropped 128x128 patches centered on each candidate with our Multi-Task ResNet-18 classifier.

| ACC/AHA Severity Tier | %DS Range | Hemodynamic Significance | Standard Clinical Action |
|---|---|---|---|
| **Mild** | < 50% | Non-flow-limiting in resting states | Optimal Medical Therapy (OMT) and lifestyle intervention |
| **Moderate** | 50% - 69% | Borderline flow limitation; inducible ischemia risk | Physiological assessment (FFR/iFR) recommended before stenting |
| **Severe** | 70% - 99% | Hemodynamically significant resting flow limitation | Percutaneous Coronary Intervention (PCI) or stenting typically indicated |
| **Occlusion** | 100% | Complete absence of antegrade coronary blood flow | Chronic Total Occlusion (CTO) protocol or urgent revascularization |

### 3.2 Reference Data Labels and %DS Derivation
Because the ARCADE benchmark dataset provided bounding box annotations without continuous %DS values or ACC/AHA severity categories, we synthesized training reference labels from bounding box dimensions using an area and aspect-ratio geometric proxy in `stenosis/data_prep/patch_dataset.py`. In our operational pipeline, we computed final %DS as a weighted combination: 0.4 * ResNet-18 regression + 0.6 * morphological caliper measurement. We explicitly noted that our reported %DS MAE (9.54%) evaluates mathematical consistency with this reference geometric proxy rather than core-lab catheterization measurements.

### 3.3 Explainable AI (XAI) via Vascular Lumen-Masked Grad-CAM
To inspect the spatial features driving our classifier, we implemented Gradient-weighted Class Activation Mapping (Grad-CAM) on `layer4` of ResNet-18. We pooled gradients of the predicted severity class score with respect to layer4 feature maps to weight each spatial activation. Because raw Grad-CAM heatmaps frequently bled into background thoracic tissue and catheter shadows, we applied an element-wise multiplication with our binary vessel mask from Milestone 2, restricting visual explanations strictly to the arterial lumen.

---

## 4. Quantitative Benchmark Results and Model Registry

### 4.1 Multi-Task ResNet-18 Test Performance (300 Angiograms)
We evaluated our Multi-Task ResNet-18 model across 300 held-out test angiograms containing 386 ground-truth lesions:

| Diagnostic Task | Evaluation Metric | Our Observed Result |
|---|---|---|
| **Binary Stenosis Detection** | Accuracy (Stenosis vs Normal) | 87.43% |
| **ACC/AHA Severity Grading** | 4-Class Classification Accuracy | 74.86% |
| **Quantitative Caliper Profiling** | %DS Mean Absolute Error (MAE) | 9.54% |

### 4.2 Faster R-CNN Candidate Detector Performance
We evaluated our standalone Faster R-CNN object detector across the 300 test angiograms at IoU >= 0.50:

| Detection Metric | Observed Value | Our Technical Analysis |
|---|---|---|
| **mAP @ IoU 0.50** | 0.0982 (9.8%) | Reflects the difficulty of anchor proposals on tiny, faint lesions |
| **Precision** | 0.0984 (9.8%) | High false-positive rate from bone contours and catheter tips |
| **Recall** | 0.1114 (11.1%) | 43 true positives detected out of 386 ground-truth lesions |
| **F1-Score** | 0.1045 | Harmonic mean of precision and recall |
| **True Positives (TP)** | 43 | Correctly localized lesion bounding boxes (IoU >= 0.50) |
| **False Positives (FP)** | 394 | Candidate proposals on non-stenotic vessel segments |

**Our Analysis of Detection Metrics:**
We observed that standard anchor-based object detectors such as Faster R-CNN face significant challenges in coronary angiography due to extreme class imbalance, tiny lesion bounding boxes (<20 pixels), and low vessel-to-background contrast, resulting in standalone recall of 11.14% (43 / 386 lesions). To overcome these missed lesions in practice, we coupled Faster R-CNN proposals with candidate regions extracted from our centerline caliber narrowing troughs (Milestone 2), ensuring that narrowings detected by diameter profiling were also evaluated by our multi-task classifier.

### 4.3 Latency Breakdown and Computational Throughput
We measured computational latency on our NVIDIA GeForce RTX 2050 laptop GPU:
- **Faster R-CNN candidate detector forward pass:** 33.55 ms (~29.8 FPS)
- **Attention U-Net segmentation forward pass:** 29.46 ms (~33.9 FPS)
- **Multi-Task ResNet-18 patch evaluation and QCA:** ~8 - 12 ms
- **Total chained sequential pipeline latency:** ~70 - 75 ms (~13 - 15 FPS)

When we executed components as decoupled modules, both the segmentation network and the detection network operated near standard fluoroscopic frame rates (15-30 FPS). When we executed the pipeline sequentially end-to-end for a single frame, throughput was approximately 14 FPS on our laptop GPU.

### 4.4 Model Checkpoint Registry

| Checkpoint File | Architecture | Parameters | Validation Metric | SHA-256 Hash |
|---|---|---|---|---|
| `best_stenosis_detector.pth` | Faster R-CNN (MobileNetV3) | ~18.9M | Val Loss: 0.182 | `55a6d5ff9c1b48d281a03f486d5d5b744b360a0058b446a0668f44ffea4a569a` |
| `best_stenosis_classifier.pth` | Multi-Task ResNet-18 | ~11.2M | Val Acc: 78.2% | `51a44e5456c6c74adcb63b151a6d48259e8790089851613eb5dafd8203f70717` |

---

## 5. Operational Clinical Workstation and Visual Evaluation

### 5.1 Web Application Diagnostic Interface
We integrated our diagnostic engine into the Next.js clinical workstation. We developed tools allowing clinicians to view angiogram cine loops, review detected candidate bounding boxes, inspect ACC/AHA severity ratings with regressed %DS values, and review lumen-masked Grad-CAM heatmaps.

### 5.2 5-Panel Clinical XAI Figures
In Figures 3.3 through 3.7, we documented 5-panel XAI explanations across five benchmark test cases: (1) Raw Angiogram; (2) Attention U-Net Mask; (3) Faster R-CNN Candidate Box; (4) Multi-Task Prediction Card; and (5) Lumen-Masked Grad-CAM Heatmap.

### 5.3 Automated Clinical Reporting, Multi-Format Export and Digital Sign-Off
To bridge deep learning inference with real-world catheterization laboratory operations, our team engineered an automated clinical reporting system. Each report includes patient demographics, coronary measurements, stenosis severity, clinical recommendations, and four-panel diagnostic visualizations. We also integrated PDF, JSON, and CSV export endpoints, along with radiologist/clinician digital sign-off and approval workflows.

Specifically, our reporting framework provides:
1. **Publication-Grade PDF Reporting:** We integrated ReportLab Platypus to compile structured 2-page clinical diagnostic summaries containing institutional letterheads, patient MRN demographics, QCA caliber morphometrics (MLD, RVD, %DS, %AS, lesion length), four-panel visual proofs (raw angiogram, Attention U-Net mask, Grad-CAM heatmap, and QCA caliber curve), ACC/AHA clinical classification, and physician signature stamps.
2. **Structured JSON Export:** We exposed an EHR-compliant REST endpoint (`/api/v1/reports/{id}/json`) streaming machine-readable JSON schemas for seamless PACS and DICOM-SR integration.
3. **Tabular Cohort CSV Analytics:** We implemented cohort and single-case CSV export (`/api/v1/reports/export/csv`) enabling researchers to perform statistical caliber audits across multiple studies.
4. **Clinician Digital Sign-Off Workflow:** We designed a secure digital sign-off endpoint (`/api/v1/reports/{id}/sign`) and UI toggle where attending radiologists and interventional cardiologists review automated findings, certify clinical validity, and apply timestamped digital approval credentials.

---

## 6. Technical Challenges and Failure Analysis

### 6.1 Deep Learning Engineering Challenges
During Milestone 3, our team resolved four key engineering challenges:
1. **Small Lesion Candidate Proposals:** When Faster R-CNN anchor proposals generated many false positives on non-stenotic vessel segments (achieving standalone precision of 9.8%), we coupled the detector with our morphological caliper narrowing troughs to help ensure candidate coverage.
2. **Class Imbalance in Patch Training:** When non-stenotic vessel segments heavily outnumbered true lesions, we applied hard negative mining and focal loss during patch generation to improve sensitivity on rare severe lesions.
3. **Grad-CAM Background Leakage:** When standard Grad-CAM produced diffuse activations spilling onto adjacent bone and catheter shadows, we applied element-wise multiplication with our binary vessel mask to restrict visual attention strictly to the arterial lumen.

### 6.2 Application Implementation Challenges
1. **Multi-Layer Canvas Synchronization:** When displaying raw cine-loop frames, binary masks, bounding boxes, and heatmaps simultaneously in the DOM caused rendering lag, we implemented off-screen HTML5 Canvas caching with alpha-blended layers, maintaining smooth playback.
2. **Consistent Component Layout:** We applied standard 2px container border styling (`border-t-2 border-[#A91121]`) across diagnostic dashboard cards.

### 6.3 Limitations and Failure Analysis
In evaluating our Milestone 3 results, we recognized several important limitations:
1. **Reference Label Proxy:** Because the ARCADE dataset did not include continuous %DS annotations, we generated reference values from bounding box dimensions via geometric heuristics. Our reported 9.54% MAE measures agreement with this geometric proxy rather than core-lab QCA or invasive FFR.
2. **Standalone Detector Sensitivity:** Faster R-CNN achieved standalone recall of 11.14% at IoU >= 0.50. Our pipeline relies on morphological caliper troughs to catch lesions missed by the anchor proposal network.
3. **Lack of Clinical Validation:** While our 9.54% %DS MAE falls within published inter-observer variability ranges in literature (8-12%), our system has not undergone live clinical validation or human-in-the-loop review by attending cardiologists.

---

## 7. Future Roadmap — 3D Reconstruction and Clinical Extensions

### 7.1 Biplane Multi-View Epipolar Geometry
Because single-plane 2D angiography cannot resolve out-of-plane vessel narrowing or true spatial geometry, we outlined future work in epipolar stereoscopic calibration to fuse two simultaneous orthogonal projections (LAO and RAO views) to reconstruct 3D lumen geometry, eliminating foreshortening errors.

### 7.2 Preoperative CCTA 3D Volume Co-Registration
We also investigated co-registering preoperative 3D CCTA volumetric scans with live 2D fluoroscopy frames to provide catheterization guidance, particularly during complex chronic total occlusion procedures.

---

## 8. Conclusion, Deliverables Inventory and Transition Plan

### 8.1 Milestone Summary
In Milestone 3, our team delivered a multi-stage stenosis detection, severity grading, and explainability pipeline for StenoVision. We trained and evaluated Faster R-CNN, Multi-Task ResNet-18, and lumen-masked Grad-CAM across 300 test angiograms. Our classifier achieved 87.43% binary accuracy, 74.86% 4-tier severity classification accuracy, and 9.54% %DS MAE against the geometric reference proxy.

### 8.2 Deliverables Inventory

| Deliverable Category | File Path | Status / Verification |
|---|---|---|
| **Detector Checkpoint** | `milestone_3_results/models/best_stenosis_detector.pth` | 151.5 MB, SHA-256 `55a6d5ff...` |
| **Classifier Checkpoint** | `milestone_3_results/models/best_stenosis_classifier.pth` | 138.2 MB, SHA-256 `51a44e54...` |
| **Test Benchmark Metrics** | `milestone_3_results/metrics/stenosis_evaluation_results.json` | Acc: 74.86%, %DS MAE: 9.54% |
| **Qualitative Figures** | `milestone_3_results/qualitative_plots/test_case_*_xai.png` | 5 high-resolution 5-panel XAI figures |
| **Diagnostic Pipeline CLI** | `stenosis/pipeline.py` | Unified CLI & Python inference engine |

### 8.3 Next Phase Transition Plan: Milestone 4
With artery segmentation, caliber analysis, stenosis detection, XAI, and automated clinical reporting (PDF, JSON, CSV export endpoints and clinician digital sign-off) functional, our team transitioned to Milestone 4: System Integration, Performance Benchmarking, and Docker Deployment.
