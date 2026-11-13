"""
StenoVision - Clinical Stenosis Severity Grader (5 Standardized Categories)
===========================================================================
Reference: Artery Segmentation & Stenosis Detection Deep Learning Platform
Official Categories:
1. Normal – No significant narrowing.
2. Mild – Mild stenosis.
3. Moderate – Moderate stenosis.
4. Severe – Significant arterial narrowing.
5. Critical – Extremely significant narrowing.
"""

from typing import Dict, Union

# Standard 5-Category Master Schema
SEVERITY_CATEGORIES = {
    "Normal": {
        "severity_code": 0,
        "category": "Normal",
        "clinical_label": "Normal – No significant narrowing.",
        "range_ds": "0% - 24%",
        "hemodynamic_significance": "Normal Vascular Patency (TIMI 3)",
        "clinical_recommendation": "No Coronary Intervention Required",
        "color_hex": "#3b82f6",  # Blue
        "bgr_tuple": (246, 130, 59),
    },
    "Mild": {
        "severity_code": 1,
        "category": "Mild",
        "clinical_label": "Mild – Mild stenosis.",
        "range_ds": "25% - 49%",
        "hemodynamic_significance": "Hemodynamically Insignificant (Non-Flow Limiting)",
        "clinical_recommendation": "Optimal Medical Therapy (OMT) & Cardiovascular Risk Factor Control",
        "color_hex": "#22c55e",  # Green
        "bgr_tuple": (94, 197, 34),
    },
    "Moderate": {
        "severity_code": 2,
        "category": "Moderate",
        "clinical_label": "Moderate – Moderate stenosis.",
        "range_ds": "50% - 69%",
        "hemodynamic_significance": "Borderline Hemodynamic Significance (Inducible Ischemia Risk)",
        "clinical_recommendation": "Fractional Flow Reserve (FFR/iFR) Physiological Evaluation Recommended",
        "color_hex": "#f59e0b",  # Amber
        "bgr_tuple": (11, 158, 245),
    },
    "Severe": {
        "severity_code": 3,
        "category": "Severe",
        "clinical_label": "Severe – Significant arterial narrowing.",
        "range_ds": "70% - 89%",
        "hemodynamic_significance": "Hemodynamically Significant (Ischemia Highly Probable)",
        "clinical_recommendation": "Percutaneous Coronary Intervention (PCI) / Revascularization Consultation",
        "color_hex": "#ef4444",  # Red
        "bgr_tuple": (68, 68, 239),
    },
    "Critical": {
        "severity_code": 4,
        "category": "Critical",
        "clinical_label": "Critical – Extremely significant narrowing.",
        "range_ds": "90% - 100%",
        "hemodynamic_significance": "Severe Flow Restriction / Critical Subtotal Occlusion (TIMI 0-1)",
        "clinical_recommendation": "Urgent Catheterization & Immediate Coronary Revascularization (PCI/CABG)",
        "color_hex": "#991b1b",  # Dark Crimson
        "bgr_tuple": (27, 27, 153),
    },
}


def grade_stenosis_severity(pct_stenosis: float) -> Dict[str, Union[str, int]]:
    """
    Classifies percentage diameter stenosis (%DS) into the 5 official categories:
    1. Normal – No significant narrowing. (<25%)
    2. Mild – Mild stenosis. (25-49%)
    3. Moderate – Moderate stenosis. (50-69%)
    4. Severe – Significant arterial narrowing. (70-89%)
    5. Critical – Extremely significant narrowing. (90-100%)
    """
    pct = float(pct_stenosis)

    if pct >= 90.0:
        base = SEVERITY_CATEGORIES["Critical"].copy()
    elif pct >= 70.0:
        base = SEVERITY_CATEGORIES["Severe"].copy()
    elif pct >= 50.0:
        base = SEVERITY_CATEGORIES["Moderate"].copy()
    elif pct >= 25.0:
        base = SEVERITY_CATEGORIES["Mild"].copy()
    else:
        base = SEVERITY_CATEGORIES["Normal"].copy()

    # Retain backward-compatible keys for existing pipelines and frontends
    base["severity_name"] = base["clinical_label"]
    base["tier"] = base["category"]
    return base
