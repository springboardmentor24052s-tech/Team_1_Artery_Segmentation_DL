"""
StenoVision - Segmentation & Vessel Analysis Inference Predictor
================================================================
Thin wrapper around milestone_2_results/predict.py allowing inference from within segmentation module.
"""

from pathlib import Path
import sys

PREDICTOR_ROOT = Path(__file__).resolve().parent.parent / "milestone_2_results"
sys.path.insert(0, str(PREDICTOR_ROOT))

from predict import StenoVisionPredictor, main  # noqa: E402

if __name__ == "__main__":
    main()

