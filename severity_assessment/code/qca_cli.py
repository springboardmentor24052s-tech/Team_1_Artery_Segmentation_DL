"""
Sub-Team 2: Localization & Severity Assessment - Member 4
Module: Standalone QCA Caliper Measurement & Severity CLI
=========================================================
Computes quantitative lumen metrics (MLD, RVD, %DS) and assigns ACC/AHA
revascularization guidance from user-specified diameters or masks.
"""

import argparse
import sys
from qca_calculator import compute_qca_metrics
from severity_grader import grade_stenosis_severity


def run_qca_cli():
    parser = argparse.ArgumentParser(description="StenoVision QCA Caliper Measurement Tool")
    parser.add_argument("--mld", type=float, required=True, help="Minimum Lumen Diameter in mm")
    parser.add_argument("--rvd", type=float, required=True, help="Reference Vessel Diameter in mm")
    parser.add_argument("--length", type=float, default=15.0, help="Lesion length in mm")

    args = parser.parse_args()

    if args.rvd <= 0:
        print("Error: Reference Vessel Diameter must be positive.")
        sys.exit(1)

    pct_ds = (1.0 - (args.mld / args.rvd)) * 100.0
    pct_ds = max(0.0, min(100.0, pct_ds))

    pct_as = (1.0 - ((args.mld / args.rvd) ** 2)) * 100.0
    pct_as = max(0.0, min(100.0, pct_as))

    grade = grade_stenosis_severity(pct_ds)

    print("\n=======================================================")
    print("QUANTITATIVE CORONARY ANGIOGRAPHY (QCA) REPORT")
    print("=======================================================")
    print(f"Minimum Lumen Diameter (MLD):      {args.mld:.2f} mm")
    print(f"Reference Vessel Diameter (RVD):    {args.rvd:.2f} mm")
    print(f"Percentage Diameter Stenosis (%DS): {pct_ds:.1f}%")
    print(f"Percentage Area Stenosis (%AS):     {pct_as:.1f}%")
    print(f"Lesion Longitudinal Length:        {args.length:.1f} mm")
    print("-------------------------------------------------------")
    tier_label = grade.get("tier") or grade.get("category", "N/A")
    hemo_signif = grade.get("hemodynamic_significance") or grade.get("hemodynamic_risk", "N/A")
    rec_action = grade.get("clinical_recommendation") or grade.get("recommendation", "N/A")

    print(f"ACC/AHA Severity Classification:    {tier_label}")
    print(f"Hemodynamic Significance:           {hemo_signif}")
    print(f"Recommended Clinical Action:        {rec_action}")
    print("=======================================================\n")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default test run
        print("Running demo calculation (MLD: 0.50 mm, RVD: 2.88 mm)...")
        sys.argv = ["qca_cli.py", "--mld", "0.50", "--rvd", "2.88", "--length", "14.8"]
    run_qca_cli()

