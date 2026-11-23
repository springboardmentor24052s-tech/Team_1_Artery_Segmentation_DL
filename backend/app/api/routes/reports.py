"""
StenoVision - Automated Clinical Reporting API Routes
======================================================
Exposes endpoints for automated report generation, PDF streaming,
structured JSON export, tabular cohort CSV export, and physician digital sign-off.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import Response

from app.services.reporting import clinical_report_service

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]])
def list_reports(
    severity: Optional[str] = Query(None, description="Filter by severity tier"),
    status: Optional[str] = Query(None, description="Filter by review status"),
    search: Optional[str] = Query(None, description="Search by case ID or patient name"),
):
    """List all available clinical analysis reports."""
    reports = clinical_report_service.get_all_reports()

    if severity and severity.lower() != "all":
        reports = [r for r in reports if r.get("severity_category", "").lower() == severity.lower()]

    if status and status.lower() != "all":
        reports = [r for r in reports if r.get("review_status", "").lower() == status.lower()]

    if search:
        s = search.lower()
        reports = [
            r for r in reports
            if s in r.get("case_id", "").lower()
            or s in r.get("patient_name", "").lower()
            or s in r.get("report_id", "").lower()
            or s in r.get("primary_vessel", "").lower()
        ]

    return reports


@router.get("/{report_id}", response_model=Dict[str, Any])
def get_report(report_id: str):
    """Retrieve full details of a specific clinical report."""
    report = clinical_report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )
    return report


@router.post("/generate/{case_id}", response_model=Dict[str, Any])
def generate_report(case_id: str, custom_findings: Optional[Dict[str, Any]] = None):
    """Dynamically generates or updates an automated report for a case."""
    report = clinical_report_service.generate_report_from_case(case_id, custom_findings)
    return report


@router.get("/{report_id}/pdf")
def download_pdf(report_id: str):
    """Download formatted publication-grade clinical PDF report."""
    report = clinical_report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found.",
        )

    pdf_bytes = clinical_report_service.generate_pdf(report)
    filename = f"StenoVision_Report_{report.get('report_id', report_id)}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.get("/{report_id}/json")
def download_json(report_id: str):
    """Export standardized machine-readable diagnostic schema in JSON."""
    report = clinical_report_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found.",
        )

    json_str = clinical_report_service.generate_json(report)
    filename = f"StenoVision_Report_{report.get('report_id', report_id)}.json"

    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.get("/export/csv")
def download_csv():
    """Download entire clinical cohort summary as tabular CSV."""
    csv_str = clinical_report_service.generate_csv_cohort()
    filename = "StenoVision_Cohort_Analytics.csv"

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.post("/{report_id}/sign", response_model=Dict[str, Any])
def toggle_sign_off(
    report_id: str,
    doctor_name: str = "Dr. Sarah Lin, MD",
    user_role: Optional[str] = Query(None, description="Active user RBAC role")
):
    """Toggles digital physician approval signature for a report. Restricted to clinical roles."""
    if user_role and user_role != "Radiologist / Clinician":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Electronic clinical sign-off is restricted to licensed Attending Radiologists / Clinicians. Technical and administrative roles cannot sign clinical reports."
        )
    report = clinical_report_service.toggle_sign_off(report_id, doctor_name)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found.",
        )
    return report
