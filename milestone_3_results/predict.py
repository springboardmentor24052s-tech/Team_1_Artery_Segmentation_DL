"""
StenoVision - Milestone 3 Unified Stenosis Detection, Severity & XAI Pipeline
=============================================================================
Unified end-to-end clinical diagnosis pipeline combining:
1. Frozen Milestone 2 Attention U-Net Artery Segmentation Engine
2. Stenosis Candidate Region Extraction & Faster R-CNN Localization
3. Multi-Task Lesion Classification & ACC/AHA Severity Grading
4. Quantitative Coronary Angiography (QCA) Caliper Engine (MLD, RVD, %DS)
5. Native PyTorch Grad-CAM Explainable AI (XAI) Saliency Generation

Usage CLI:
    python StenoVision/stenosis/pipeline.py --image "sample.png" --output-dir "./results"
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "milestone_2_results"))

from stenosis.data_prep.candidate_extractor import extract_stenosis_candidates_from_mask
from stenosis.models.detector import build_stenosis_detector
from stenosis.models.multi_task_resnet import MultiTaskStenosisResNet18
from stenosis.localization.postprocessor import filter_and_suppress_detections
from stenosis.localization.branch_mapper import map_lesion_to_coronary_branch
from stenosis.severity.qca_calculator import compute_qca_metrics
from stenosis.severity.severity_grader import grade_stenosis_severity
from stenosis.xai.grad_cam import GradCAM
from stenosis.xai.visualizer import generate_5panel_xai_figure
try:
    from milestone_2_results.predict import StenoVisionPredictor
except (ImportError, AttributeError):
    try:
        import importlib.util
        _spec = importlib.util.spec_from_file_location("m2_pred_mod", PROJECT_ROOT / "milestone_2_results" / "predict.py")
        _m2_mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_m2_mod)
        StenoVisionPredictor = _m2_mod.StenoVisionPredictor
    except Exception:
        from predict import StenoVisionPredictor


class StenoVisionDiagnosticPipeline:
    """Production-ready end-to-end diagnostic pipeline for StenoVision Milestone 3."""

    def __init__(self, device: Optional[str] = None):
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        print(f"Initializing StenoVision Diagnostic Pipeline on {self.device}...")

        CURRENT_DIR = Path(__file__).resolve().parent

        # 1. Segmentation prior
        self.seg_predictor = StenoVisionPredictor(device=str(self.device))

        # 2. Faster R-CNN Detector (prioritize local models/)
        det_local = CURRENT_DIR / "models" / "best_stenosis_detector.pth"
        det_repo = PROJECT_ROOT / "stenosis" / "checkpoints" / "best_stenosis_detector.pth"
        det_path = det_local if det_local.exists() else det_repo
        print(f"Loading detector checkpoint from: {det_path}")
        self.detector = build_stenosis_detector(num_classes=2, pretrained_backbone=False).to(self.device)
        det_ckpt = torch.load(det_path, map_location=self.device)
        self.detector.load_state_dict(det_ckpt["model_state_dict"] if "model_state_dict" in det_ckpt else det_ckpt)
        self.detector.eval()

        # 3. Multi-Task Classifier & XAI (prioritize local models/)
        cls_local = CURRENT_DIR / "models" / "best_stenosis_classifier.pth"
        cls_repo = PROJECT_ROOT / "stenosis" / "checkpoints" / "best_stenosis_classifier.pth"
        cls_path = cls_local if cls_local.exists() else cls_repo
        print(f"Loading classifier checkpoint from: {cls_path}")
        self.classifier = MultiTaskStenosisResNet18(in_channels=1).to(self.device)
        cls_ckpt = torch.load(cls_path, map_location=self.device)
        self.classifier.load_state_dict(cls_ckpt["model_state_dict"] if "model_state_dict" in cls_ckpt else cls_ckpt)
        self.classifier.eval()

        self.gradcam = GradCAM(self.classifier, self.classifier.get_gradcam_target_layer())
        print("Pipeline initialized successfully.")

    def diagnose(
        self,
        image_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        save_xai_plots: bool = True,
    ) -> Dict:
        """
        Executes end-to-end diagnosis on a single X-ray Coronary Angiogram.
        """
        path = Path(image_path)
        img_gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img_gray is None:
            raise FileNotFoundError(f"Could not load image: {path}")

        t0 = time.perf_counter()

        # Step 1: Artery Tree Segmentation & Medial Skeleton
        seg_res = self.seg_predictor.predict(path)
        vessel_mask = seg_res["clean_mask"]
        skeleton = seg_res["skeleton"]

        # Step 2: Geometric Caliper Candidate Extraction
        caliper_cands = extract_stenosis_candidates_from_mask(vessel_mask, narrowing_threshold=0.30)

        # Step 3: Whole-Image Faster R-CNN Detection
        img_512 = cv2.resize(img_gray, (512, 512)).astype(np.float32) / 255.0
        img_rgb = np.stack([img_512]*3, axis=0)
        img_tensor = torch.from_numpy(img_rgb).float().unsqueeze(0).to(self.device)

        with torch.no_grad():
            preds = self.detector(img_tensor)

        p_boxes = preds[0]["boxes"].cpu().numpy()
        p_scores = preds[0]["scores"].cpu().numpy()
        p_labels = preds[0]["labels"].cpu().numpy()

        det_proposals = filter_and_suppress_detections(
            p_boxes, p_scores, p_labels, score_threshold=0.045, nms_iou_threshold=0.30
        )

        # Fuse proposals from both candidate extractor and detector
        all_candidate_boxes = [d["bbox"] for d in det_proposals]
        for c in caliper_cands:
            all_candidate_boxes.append(c["bbox"])

        # Deduplicate candidate boxes
        if len(all_candidate_boxes) > 0:
            dummy_scores = np.ones(len(all_candidate_boxes))
            dummy_labels = np.ones(len(all_candidate_boxes))
            merged_candidates = filter_and_suppress_detections(
                np.array(all_candidate_boxes), dummy_scores, dummy_labels, score_threshold=0.5, nms_iou_threshold=0.25
            )
        else:
            merged_candidates = []

        # Step 4: Multi-Task Classification & Severity Grading
        findings = []
        for idx, cand in enumerate(merged_candidates):
            cx, cy = cand["centroid"]
            half = 64
            x1 = max(0, cx - half)
            y1 = max(0, cy - half)
            x2 = min(img_gray.shape[1], cx + half)
            y2 = min(img_gray.shape[0], cy + half)

            patch = img_gray[y1:y2, x1:x2]
            if patch.shape != (128, 128):
                patch = cv2.resize(patch, (128, 128))

            p_norm = (patch.astype(np.float32) - patch.min()) / (patch.max() - patch.min() + 1e-8)
            p_tensor = torch.from_numpy(p_norm).unsqueeze(0).unsqueeze(0).float().to(self.device)

            with torch.no_grad():
                out = self.classifier(p_tensor)

            prob_stenosis = float(torch.softmax(out["binary_logits"], dim=1)[0, 1].item())
            sev_idx = int(torch.argmax(out["severity_logits"], dim=1).item())
            est_narrowing = float(out["pct_narrowing"].item())

            # Clinical QCA calculation
            qca = compute_qca_metrics(vessel_mask, cand["bbox"])
            branch = map_lesion_to_coronary_branch(cand["centroid"])
            # Blend neural predicted %DS with geometric QCA
            final_pct = round(0.6 * qca["pct_stenosis"] + 0.4 * est_narrowing, 1)
            sev = grade_stenosis_severity(final_pct)

            finding = {
                "lesion_id": idx + 1,
                "bbox": cand["bbox"],
                "centroid": cand["centroid"],
                "probability_stenosis": round(prob_stenosis, 3),
                "qca_metrics": {
                    "mld_mm": qca["mld_mm"],
                    "rvd_mm": qca["rvd_mm"],
                    "pct_stenosis": final_pct,
                    "lesion_length_mm": qca["lesion_length_mm"],
                },
                "coronary_branch": branch["branch_name"],
                "segment_code": branch["segment_code"],
                "severity_grade": sev["severity_name"],
                "severity_tier": sev["tier"],
                "hemodynamic_significance": sev["hemodynamic_significance"],
                "clinical_recommendation": sev["clinical_recommendation"],
                "color_hex": sev["color_hex"],
            }
            findings.append(finding)

        if self.device.type == "cuda":
            torch.cuda.synchronize()
        latency_ms = (time.perf_counter() - t0) * 1000.0

        # Step 5: Generate XAI figure for top lesion if requested
        xai_plot_path = None
        if save_xai_plots and len(findings) > 0 and output_dir:
            out_p = Path(output_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            top_f = findings[0]
            cx, cy = top_f["centroid"]
            half = 64
            x1 = max(0, cx - half)
            y1 = max(0, cy - half)
            x2 = min(img_gray.shape[1], cx + half)
            y2 = min(img_gray.shape[0], cy + half)
            patch = img_gray[y1:y2, x1:x2]
            if patch.shape != (128, 128):
                patch = cv2.resize(patch, (128, 128))

            p_norm = (patch.astype(np.float32) - patch.min()) / (patch.max() - patch.min() + 1e-8)
            p_tensor = torch.from_numpy(p_norm).unsqueeze(0).unsqueeze(0).float().to(self.device)

            with torch.enable_grad():
                cam_norm, heatmap_bgr = self.gradcam.generate_heatmap(p_tensor, task_head="severity_logits")
            xai_plot_path = out_p / f"{path.stem}_xai_explanation.png"

            det_info_for_vis = {
                "bbox": top_f["bbox"],
                "centroid": top_f["centroid"],
                "confidence": top_f["probability_stenosis"],
                "branch_name": top_f["coronary_branch"],
                "severity_name": top_f["severity_grade"],
                "tier": top_f["severity_tier"],
                "bgr_tuple": (68, 68, 239) if top_f["severity_tier"] == "Severe" else (11, 158, 245),
            }

            generate_5panel_xai_figure(
                image_gray=img_gray,
                vessel_mask=vessel_mask,
                centerline=skeleton,
                detection_info=det_info_for_vis,
                lesion_patch=patch,
                gradcam_heatmap=heatmap_bgr,
                qca_info=top_f["qca_metrics"],
                save_path=xai_plot_path,
                case_title=f"Angiogram Diagnosis ({path.name})",
            )

        report = {
            "image": str(path.resolve()),
            "total_lesions_detected": len(findings),
            "findings": findings,
            "overall_assessment": findings[0]["severity_grade"] if len(findings) > 0 else "Normal Vessel (No Stenosis)",
            "primary_action": findings[0]["clinical_recommendation"] if len(findings) > 0 else "No intervention required",
            "latency_ms": round(latency_ms, 2),
            "xai_explanation_plot": str(xai_plot_path.resolve()) if xai_plot_path else None,
        }

        if output_dir:
            out_p = Path(output_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            with open(out_p / f"{path.stem}_diagnostic_report.json", "w") as f:
                json.dump(report, f, indent=2)

        return report


def main():
    parser = argparse.ArgumentParser(description="StenoVision Milestone 3 Stenosis Diagnostic Pipeline")
    parser.add_argument("--image", type=str, required=True, help="Path to input XCA image.")
    parser.add_argument("--output-dir", type=str, default="./diagnostic_results", help="Directory to save diagnosis.")
    parser.add_argument("--device", type=str, default="cuda", help="'cuda' or 'cpu'")
    args = parser.parse_args()

    pipeline = StenoVisionDiagnosticPipeline(device=args.device)
    res = pipeline.diagnose(args.image, output_dir=args.output_dir)

    print("\n" + "=" * 65)
    print("STENOVISION CLINICAL DIAGNOSTIC REPORT")
    print("=" * 65)
    print(f"Image:                 {Path(res['image']).name}")
    print(f"Total Lesions:         {res['total_lesions_detected']}")
    print(f"Overall Assessment:    {res['overall_assessment']}")
    print(f"Recommended Action:    {res['primary_action']}")
    print(f"Inference Latency:     {res['latency_ms']} ms")
    if res['xai_explanation_plot']:
        print(f"XAI Explanation Card:  {res['xai_explanation_plot']}")
    print("=" * 65)


if __name__ == "__main__":
    main()
