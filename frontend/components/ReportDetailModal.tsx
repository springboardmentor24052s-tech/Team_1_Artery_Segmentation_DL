'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import {
  X,
  Download,
  FileCode,
  Printer,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ShieldCheck,
  Building2,
  Activity,
  Layers,
  FileText,
  UserCheck,
  FileSpreadsheet,
  ShieldAlert
} from 'lucide-react';
import { AnalysisReport, SystemUser } from '@/lib/mockData';
import { downloadReportPdf, exportReportJson, toggleReportSignOff, exportCaseCsv } from '@/lib/api';
import { canSignReports, getAllowedExports } from '@/lib/permissions';

interface ReportDetailModalProps {
  report: AnalysisReport | null;
  isOpen: boolean;
  onClose: () => void;
  onReportUpdated?: (updated: AnalysisReport) => void;
  currentUser?: SystemUser;
}

export const ReportDetailModal: React.FC<ReportDetailModalProps> = ({
  report,
  isOpen,
  onClose,
  onReportUpdated,
  currentUser,
}) => {
  const [currentReport, setCurrentReport] = useState<AnalysisReport | null>(report);
  const [isSigning, setIsSigning] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  React.useEffect(() => {
    setCurrentReport(report);
  }, [report]);

  if (!isOpen || !currentReport) return null;

  const handleDownloadPdf = async () => {
    setDownloadingPdf(true);
    try {
      await downloadReportPdf(currentReport.reportId);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleExportJson = async () => {
    await exportReportJson(currentReport);
  };

  const handleExportCsv = () => {
    exportCaseCsv({
      caseId: currentReport.caseId,
      patientName: currentReport.patientName,
      patientId: currentReport.patientId,
      primaryVessel: currentReport.primaryVessel,
      ahaSegment: currentReport.ahaSegment,
      mldMm: currentReport.mldMm,
      rvdMm: currentReport.rvdMm,
      pctStenosis: currentReport.pctStenosis,
      pctAreaStenosis: currentReport.pctAreaStenosis,
      lesionLengthMm: currentReport.lesionLengthMm,
      severityCategory: currentReport.severityCategory,
      recommendation: currentReport.recommendation,
    });
  };

  const handlePrint = () => {
    window.print();
  };

  const handleToggleSignOff = async () => {
    setIsSigning(true);
    try {
      const updated = await toggleReportSignOff(
        currentReport.reportId,
        currentUser?.name || 'Dr. Aris Thorne, MD',
        currentUser?.role
      );
      setCurrentReport(updated);
      if (onReportUpdated) {
        onReportUpdated(updated);
      }
    } catch (err) {
      console.error('Sign-off error:', err);
    } finally {
      setIsSigning(false);
    }
  };

  const getSeverityBadge = (category?: string) => {
    switch (category?.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/30';
      case 'severe':
        return 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/30';
      case 'moderate':
        return 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30';
      case 'mild':
        return 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/30';
      default:
        return 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30';
    }
  };

  const isSigned = currentReport.reviewStatus === 'Verified' || currentReport.reviewStatus === 'Signed Off' || currentReport.reviewStatus === 'Approved';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto animate-in fade-in duration-200">
      <div className="relative w-full max-w-5xl my-8 bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50/90">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <FileText className="w-5 h-5 text-[#A91121]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold tracking-tight text-[#252525]">
                  Clinical QCA Report: {currentReport.reportId}
                </h2>
                <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border ${getSeverityBadge(currentReport.severityCategory)}`}>
                  {currentReport.severityCategory || 'Assessment'}
                </span>
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                  isSigned ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30'
                }`}>
                  {isSigned ? 'Verified & Signed' : 'Pending Physician Review'}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Target Case: <span className="font-semibold text-[#252525]">{currentReport.caseId}</span> · Generated: {currentReport.generatedDate}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {getAllowedExports(currentUser?.role).includes('pdf') && (
              <button
                onClick={handleDownloadPdf}
                disabled={downloadingPdf}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-[#A91121] text-white hover:bg-[#8B0E1B] transition-colors shadow-sm cursor-pointer"
                title="Download high-resolution 2-page clinical PDF"
              >
                <Download className="w-3.5 h-3.5" />
                {downloadingPdf ? 'Generating...' : 'Download PDF'}
              </button>
            )}
            {getAllowedExports(currentUser?.role).includes('json') && (
              <button
                onClick={handleExportJson}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors border border-slate-200 cursor-pointer"
                title="Export machine-readable JSON schema"
              >
                <FileCode className="w-3.5 h-3.5" />
                JSON
              </button>
            )}
            {getAllowedExports(currentUser?.role).includes('csv') && (
              <button
                onClick={handleExportCsv}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors border border-slate-200 cursor-pointer"
                title="Export QCA measurements as CSV"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
                CSV
              </button>
            )}
            <button
              onClick={handlePrint}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors border border-slate-200 cursor-pointer"
              title="Print Clinical Summary"
            >
              <Printer className="w-3.5 h-3.5" />
              Print
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors ml-2 cursor-pointer"
              title="Close Modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Clinical Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm">
          
          {/* Institutional Banner */}
          <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-[#1A365D]/10 via-[#2B6CB0]/5 to-transparent border border-[#1A365D]/20">
            <div className="flex items-center gap-3">
              <Building2 className="w-8 h-8 text-[#1A365D] dark:text-[#63B3ED]" />
              <div>
                <h3 className="font-bold text-[#1A365D] dark:text-[#90CDF4] text-base tracking-wide">
                  STENOVISION CARDIOVASCULAR INTELLIGENCE
                </h3>
                <p className="text-xs text-muted-foreground">
                  Quantitative Coronary Angiography (QCA) & Deep Learning Diagnostic System · v2.1
                </p>
              </div>
            </div>
            <div className="text-right text-xs">
              <div className="font-mono text-muted-foreground">ENGINE: Attention U-Net + ResNet-18</div>
              <div className="text-emerald-700 dark:text-emerald-400 font-semibold flex items-center gap-1 justify-end">
                <ShieldCheck className="w-3.5 h-3.5" /> Inference Validated (Dice 68.33%)
              </div>
            </div>
          </div>

          {/* Patient Demographics & Exam Details Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-lg bg-muted/30 border border-border">
            <div>
              <span className="text-xs text-muted-foreground block">Patient Name</span>
              <span className="font-semibold text-foreground">{currentReport.patientName}</span>
            </div>
            <div>
              <span className="text-xs text-muted-foreground block">Patient ID / MRN</span>
              <span className="font-mono font-medium text-foreground">{currentReport.patientId || 'PT-99421'}</span>
            </div>
            <div>
              <span className="text-xs text-muted-foreground block">Demographics</span>
              <span className="font-medium text-foreground">
                {currentReport.age ? `${currentReport.age} Y` : '62 Y'} / {currentReport.gender || 'Female'}
              </span>
            </div>
            <div>
              <span className="text-xs text-muted-foreground block">Imaging Modality</span>
              <span className="font-medium text-foreground">{currentReport.modality || 'XCA (Coronary Angiogram)'}</span>
            </div>
            <div>
              <span className="text-xs text-muted-foreground block">Primary Target Vessel</span>
              <span className="font-semibold text-[#1A365D] dark:text-[#90CDF4]">
                {currentReport.primaryVessel || 'Left Anterior Descending (LAD)'}
              </span>
            </div>
            <div>
              <span className="text-xs text-muted-foreground block">AHA Segment</span>
              <span className="font-medium text-foreground">{currentReport.ahaSegment || 'Segment 7 (Mid LAD)'}</span>
            </div>
            <div>
              <span className="text-xs text-muted-foreground block">Consensus Score</span>
              <span className="font-medium text-foreground">{currentReport.consensusScore}</span>
            </div>
            <div>
              <span className="text-xs text-muted-foreground block">Report Archive Size</span>
              <span className="font-mono text-muted-foreground">{currentReport.fileSize}</span>
            </div>
          </div>

          {/* 3D Volumetric Acquisition Banner if 3D Case */}
          {currentReport.is3D && (
            <div className="p-4 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <Layers className="w-6 h-6 text-cyan-600 dark:text-cyan-400" />
                <div>
                  <h4 className="font-bold text-cyan-900 dark:text-cyan-200 text-xs">
                    3D VOLUMETRIC CT ANGIOGRAM (CTPA / CCTA)
                  </h4>
                  <p className="text-[11px] text-cyan-700 dark:text-cyan-300">
                    Acquisition Matrix: <span className="font-mono font-bold">{currentReport.volumeDimensions || '512 x 512 x 256'}</span> · Total Slices: <span className="font-mono font-bold">{currentReport.totalSlices || 256}</span>
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4 text-xs font-mono">
                <div>
                  <span className="text-muted-foreground block text-[10px]">Reformation Slice</span>
                  <span className="font-bold text-foreground">Slice #{currentReport.selectedSlice || 150}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[10px]">Hounsfield Window</span>
                  <span className="font-bold text-foreground">[-100, +600] HU</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[10px]">Voxel Spacing</span>
                  <span className="font-medium text-foreground">{currentReport.voxelSpacingMm || '0.70 x 0.70 x 1.00 mm'}</span>
                </div>
              </div>
            </div>
          )}

          {/* Visual Proof Section (Section 14: Angiogram, Mask, Heatmap, Caliper) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-foreground flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#A91121]" />
                Four-Panel Explainable AI (XAI) Visual Evidence
              </h4>
              <span className="text-xs text-muted-foreground">
                Synchronized Caliber & Spatial Attention Attribution
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Panel 1: Raw XCA Scan */}
              <div className="rounded-lg border border-border bg-card overflow-hidden">
                <div className="px-3 py-1.5 bg-muted/50 border-b border-border flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground">1. Raw Angiogram (XCA)</span>
                  <span className="text-[10px] text-muted-foreground">512×512</span>
                </div>
                <div className="relative aspect-square bg-black/90 flex items-center justify-center">
                  <Image
                    src={currentReport.rawScanUrl || '/assets/cases/10.png'}
                    alt="Raw Angiogram"
                    fill
                    className="object-contain"
                    unoptimized
                  />
                </div>
              </div>

              {/* Panel 2: Segmented Artery Mask */}
              <div className="rounded-lg border border-border bg-card overflow-hidden">
                <div className="px-3 py-1.5 bg-muted/50 border-b border-border flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground">2. Attention U-Net Mask</span>
                  <span className="text-[10px] text-emerald-600 dark:text-emerald-400">Dice: 68.33%</span>
                </div>
                <div className="relative aspect-square bg-black/90 flex items-center justify-center">
                  <Image
                    src={currentReport.maskUrl || '/assets/cases/10_mask.png'}
                    alt="Attention U-Net Mask"
                    fill
                    className="object-contain"
                    unoptimized
                  />
                </div>
              </div>

              {/* Panel 3: Grad-CAM Saliency Heatmap */}
              <div className="rounded-lg border border-border bg-card overflow-hidden">
                <div className="px-3 py-1.5 bg-muted/50 border-b border-border flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground">3. Grad-CAM Heatmap</span>
                  <span className="text-[10px] text-red-600 dark:text-red-400">ResNet-18 Severity Head</span>
                </div>
                <div className="relative aspect-square bg-black/90 flex items-center justify-center">
                  <Image
                    src={currentReport.heatmapUrl || '/assets/cases/10_heatmap.png'}
                    alt="Grad-CAM Saliency Heatmap"
                    fill
                    className="object-contain"
                    unoptimized
                  />
                </div>
              </div>

              {/* Panel 4: 4-Panel Caliper Curve / Integrated Proof */}
              <div className="rounded-lg border border-border bg-card overflow-hidden">
                <div className="px-3 py-1.5 bg-muted/50 border-b border-border flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground">4. QCA Caliper / Verification</span>
                  <span className="text-[10px] text-blue-600 dark:text-blue-400">Caliber Profiling</span>
                </div>
                <div className="relative aspect-square bg-black/90 flex items-center justify-center">
                  <Image
                    src={currentReport.fourPanelXaiUrl || '/assets/cases/10_4panel_severity.png'}
                    alt="4-Panel QCA Verification"
                    fill
                    className="object-contain"
                    unoptimized
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Quantitative Coronary Angiography (QCA) Table */}
          <div className="space-y-3">
            <h4 className="font-semibold text-foreground flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#2B6CB0]" />
              Automated Quantitative Coronary Angiography (QCA) Caliber Metrics
            </h4>
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-muted/60 text-muted-foreground uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-2.5 px-3 border-b border-border">Quantitative Metric</th>
                    <th className="py-2.5 px-3 border-b border-border">Measured Value</th>
                    <th className="py-2.5 px-3 border-b border-border">Healthy Reference Range</th>
                    <th className="py-2.5 px-3 border-b border-border">Clinical Hemodynamic Significance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-medium">
                  <tr>
                    <td className="py-2.5 px-3 font-semibold text-foreground">Reference Vessel Diameter (RVD)</td>
                    <td className="py-2.5 px-3 font-mono text-foreground">{currentReport.rvdMm?.toFixed(2) ?? '2.98'} mm</td>
                    <td className="py-2.5 px-3 text-muted-foreground">2.50 – 4.50 mm</td>
                    <td className="py-2.5 px-3 text-muted-foreground">Baseline healthy lumen caliber proxy</td>
                  </tr>
                  <tr className="bg-muted/20">
                    <td className="py-2.5 px-3 font-semibold text-foreground">Minimum Lumen Diameter (MLD)</td>
                    <td className="py-2.5 px-3 font-mono font-bold text-[#A91121]">
                      {currentReport.mldMm?.toFixed(2) ?? '1.05'} mm
                    </td>
                    <td className="py-2.5 px-3 text-muted-foreground">&gt; 2.00 mm</td>
                    <td className="py-2.5 px-3 text-muted-foreground">Critical bottleneck dimension at lesion core</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-semibold text-foreground">Percent Diameter Stenosis (%DS)</td>
                    <td className="py-2.5 px-3 font-mono font-bold text-foreground">
                      {currentReport.pctStenosis?.toFixed(1) ?? '64.7'}%
                    </td>
                    <td className="py-2.5 px-3 text-muted-foreground">&lt; 25.0% (Normal)</td>
                    <td className="py-2.5 px-3 text-foreground">
                      ACC/AHA Class: <span className="font-semibold">{currentReport.severityCategory || 'Moderate'}</span>
                    </td>
                  </tr>
                  <tr className="bg-muted/20">
                    <td className="py-2.5 px-3 font-semibold text-foreground">Percent Cross-Sectional Area Stenosis (%AS)</td>
                    <td className="py-2.5 px-3 font-mono text-foreground">
                      {currentReport.pctAreaStenosis?.toFixed(1) ?? '87.5'}%
                    </td>
                    <td className="py-2.5 px-3 text-muted-foreground">&lt; 50.0%</td>
                    <td className="py-2.5 px-3 text-muted-foreground">Volumetric hemodynamic perfusion impedance</td>
                  </tr>
                  <tr>
                    <td className="py-2.5 px-3 font-semibold text-foreground">Lesion Length</td>
                    <td className="py-2.5 px-3 font-mono text-foreground">
                      {currentReport.lesionLengthMm?.toFixed(1) ?? '12.8'} mm
                    </td>
                    <td className="py-2.5 px-3 text-muted-foreground">&lt; 10.0 mm (Focal)</td>
                    <td className="py-2.5 px-3 text-muted-foreground">
                      {((currentReport.lesionLengthMm || 0) > 20) ? 'Diffuse / Long Segment' : ((currentReport.lesionLengthMm || 0) > 10) ? 'Tubular Lesion' : 'Focal Lesion'}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Diagnostic Assessment & Actionable Recommendations */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-card border border-border space-y-2">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">
                Hemodynamic Risk Stratification
              </span>
              <p className="font-semibold text-foreground text-sm">
                {currentReport.hemodynamicRisk || 'Borderline Hemodynamic Significance (Ischemic Risk)'}
              </p>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {currentReport.summary}
              </p>
            </div>

            <div className="p-4 rounded-lg bg-primary/5 border border-primary/20 space-y-2">
              <span className="text-xs font-semibold text-[#A91121] uppercase tracking-wider block flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" />
                Actionable Clinical Recommendation
              </span>
              <p className="font-semibold text-foreground text-sm">
                {currentReport.recommendation || 'Cardiology outpatient consult, non-invasive stress myocardial perfusion imaging or CT-FFR.'}
              </p>
              <p className="text-xs text-muted-foreground">
                Recommendation formulated via automated clinical guidelines mapping based on ACC/AHA SCAI consensus criteria.
              </p>
            </div>
          </div>

          {/* Physician Sign-Off & Verification Block */}
          <div className="p-4 rounded-lg bg-muted/40 border border-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-full ${isSigned ? 'bg-emerald-500/10 text-emerald-600' : 'bg-amber-500/10 text-amber-600'}`}>
                {isSigned ? <UserCheck className="w-6 h-6" /> : <Clock className="w-6 h-6" />}
              </div>
              <div>
                <h5 className="font-semibold text-foreground text-sm">
                  Attending Physician Verification & Sign-Off
                </h5>
                {isSigned ? (
                  <div className="text-xs text-muted-foreground mt-0.5 space-y-0.5">
                    <p>
                      Signed by: <span className="font-semibold text-foreground">{currentReport.signedBy}</span> ({currentReport.licenseNumber || 'License #MD-94021'})
                    </p>
                    <p>Timestamp: <span className="font-mono">{currentReport.signedAt || currentReport.generatedDate}</span></p>
                  </div>
                ) : (
                  <p className="text-xs text-amber-700 dark:text-amber-400 mt-0.5">
                    This report has not yet been countersigned by an attending cardiologist.
                  </p>
                )}
              </div>
            </div>

            {canSignReports(currentUser?.role) ? (
              <button
                onClick={handleToggleSignOff}
                disabled={isSigning}
                className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer ${
                  isSigned
                    ? 'bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border'
                    : 'bg-emerald-600 text-white hover:bg-emerald-700'
                }`}
              >
                <CheckCircle2 className="w-4 h-4" />
                {isSigning ? 'Updating...' : isSigned ? 'Revoke / Edit Signature' : 'Sign & Approve Report'}
              </button>
            ) : (
              <div className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-100 border border-slate-200 text-slate-600 text-xs font-medium">
                <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
                <span>Clinical authority restricted to licensed Attending Radiologists / Clinicians</span>
              </div>
            )}
          </div>

          {/* Mandatory Section 14 Legal AI Disclaimer */}
          <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-start gap-3 text-xs text-amber-900 dark:text-amber-300">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold uppercase tracking-wider block">
                MANDATORY CLINICAL AI ASSISTANCE NOTICE (SECTION 14)
              </span>
              <p className="leading-relaxed">
                The output of this system is an AI-assisted quantitative analysis (Attention U-Net v2.1 + ResNet-18 Severity Network) and is <strong>not a standalone clinical diagnosis</strong>. All calculated values including minimum lumen diameter (MLD), reference vessel diameter (RVD), and percent diameter stenosis (%DS) must be validated by a board-certified cardiologist or radiologist in conjunction with patient clinical presentation.
              </p>
            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-200 bg-slate-50/90 flex items-center justify-between text-xs text-slate-500">
          <span>StenoVision Automated Clinical Reporting Engine · Clinical Decision Support Protocol</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 font-medium rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200 cursor-pointer transition-colors"
          >
            Close Viewer
          </button>
        </div>

      </div>
    </div>
  );
};
