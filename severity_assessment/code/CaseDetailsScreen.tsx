'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { INITIAL_CASES, MedicalCase } from '@/lib/mockData';
import { StatusIndicator } from '../StatusIndicator';
import {
  FileText,
  Download,
  CheckCircle2,
  ArrowLeft,
  Eye,
  Layers,
  Activity,
  Sliders,
  ZoomIn,
  AlertTriangle
} from 'lucide-react';

interface CaseDetailsScreenProps {
  caseId?: string;
  onNavigate: (screen: string) => void;
}

export const CaseDetailsScreen: React.FC<CaseDetailsScreenProps> = ({ caseId = 'CASE-1010', onNavigate }) => {
  const currentCase: MedicalCase = INITIAL_CASES.find((c) => c.id === caseId) || INITIAL_CASES[0];
  const [selectedView, setSelectedView] = useState<'quad-xai' | 'caliper-card' | 'raw-scan' | 'saliency' | 'segmentation'>('quad-xai');
  const [reviewStatus, setReviewStatus] = useState<'Pending' | 'Approved'>('Pending');

  const xaiCard = currentCase.xaiCardUrl || '/assets/cases/10_xai_explanation.png';
  const rawScan = currentCase.rawScanUrl || '/assets/cases/10.png';

  return (
    <div className="space-y-6">
      {/* Back button & Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('cases')}
            className="p-2 bg-white border border-[#A91121]/20 hover:bg-[#F5F5F5] text-[#252525] rounded-lg transition-colors"
            title="Back to Case Repository"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-[#252525]">Case Investigation: {currentCase.id}</h2>
              <span className="font-mono text-xs font-semibold px-2 py-0.5 bg-[#A91121]/10 text-[#A91121] rounded border border-[#A91121]/20">
                {currentCase.patientId}
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Patient: <span className="font-semibold text-[#252525]">{currentCase.patientName}</span> ({currentCase.age}y / {currentCase.gender}) · Ingested {currentCase.uploadDate}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setReviewStatus('Approved');
              alert(`Clinical sign-off recorded for ${currentCase.id}`);
            }}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 shadow-sm ${
              reviewStatus === 'Approved' ? 'bg-emerald-600 text-white' : 'bg-[#A91121] hover:bg-[#800D1B] text-white'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            {reviewStatus === 'Approved' ? 'Sign-Off Recorded' : 'Approve Clinical Findings'}
          </button>
        </div>
      </div>

      {/* Main Grid: Multi-Layer Diagnostic Viewer + Case Properties */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Diagnostic Angiogram Viewer (2 cols) */}
        <div className="lg:col-span-2 bg-white border border-[#A91121]/20 rounded-xl overflow-hidden flex flex-col shadow-sm">
          {/* Viewer Toolbar */}
          <div className="h-12 bg-[#F8F9FA] border-b border-[#A91121]/15 px-4 flex items-center justify-between text-xs text-slate-700 flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold text-[#252525]">Diagnostic Angiogram Viewer</span>
              <span className="text-slate-300">·</span>
              <div className="flex bg-[#EFEFEF] p-0.5 rounded-lg border border-[#A91121]/20 flex-wrap gap-1">
                <button
                  onClick={() => setSelectedView('quad-xai')}
                  className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-colors ${
                    selectedView === 'quad-xai' ? 'bg-[#A91121] text-white shadow-xs' : 'text-slate-600 hover:text-[#252525]'
                  }`}
                >
                  Clinical Quad-View
                </button>
                <button
                  onClick={() => setSelectedView('caliper-card')}
                  className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-colors ${
                    selectedView === 'caliper-card' ? 'bg-[#A91121] text-white shadow-xs' : 'text-slate-600 hover:text-[#252525]'
                  }`}
                >
                  Quantitative QCA Caliper View
                </button>
                <button
                  onClick={() => setSelectedView('raw-scan')}
                  className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-colors ${
                    selectedView === 'raw-scan' ? 'bg-[#A91121] text-white shadow-xs' : 'text-slate-600 hover:text-[#252525]'
                  }`}
                >
                  Original Angiogram Scan
                </button>
                <button
                  onClick={() => setSelectedView('saliency')}
                  className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-colors flex items-center gap-1 ${
                    selectedView === 'saliency' ? 'bg-[#A91121] text-white shadow-xs' : 'text-slate-600 hover:text-[#252525]'
                  }`}
                >
                  <Activity className="w-3 h-3" /> Grad-CAM Saliency
                </button>
                <button
                  onClick={() => setSelectedView('segmentation')}
                  className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-colors ${
                    selectedView === 'segmentation' ? 'bg-[#A91121] text-white shadow-xs' : 'text-slate-600 hover:text-[#252525]'
                  }`}
                >
                  Artery Mask Tree
                </button>
              </div>
            </div>

            <div className="font-mono text-[11px] text-slate-500 hidden sm:block">
              {currentCase.scanType} · 512x512
            </div>
          </div>

          {/* Viewer Stage */}
          <div className="relative flex-1 min-h-[380px] bg-[#111315] flex flex-col items-center justify-center p-4">
            {selectedView === 'quad-xai' && (
              <div className="relative w-full h-[360px]">
                <Image
                  src={currentCase.fourPanelXaiUrl || '/assets/cases/10_4panel_xai.png'}
                  alt={`Case ${currentCase.id} Clinical Diagnostic Quad-View`}
                  fill
                  className="object-contain"
                  unoptimized
                />
              </div>
            )}

            {selectedView === 'caliper-card' && (
              <div className="relative w-full h-[360px]">
                <Image
                  src={xaiCard}
                  alt={`Case ${currentCase.id} Quantitative QCA Caliper explanation`}
                  fill
                  className="object-contain"
                  unoptimized
                />
              </div>
            )}

            {selectedView === 'raw-scan' && (
              <div className="relative w-full h-[360px]">
                <Image
                  src={rawScan}
                  alt={`Case ${currentCase.id} original coronary angiogram scan`}
                  fill
                  className="object-contain"
                  unoptimized
                />
              </div>
            )}

            {selectedView === 'saliency' && (
              <div className="relative w-full h-[360px] flex items-center justify-center">
                <Image
                  src={currentCase.heatmapUrl || rawScan}
                  alt={`Case ${currentCase.id} with Grad-CAM Saliency`}
                  fill
                  className="object-contain"
                  unoptimized
                />
                <div className="absolute bottom-3 left-4 pointer-events-none">
                  <span className="font-mono text-xs font-bold text-amber-300 bg-slate-900/85 px-3 py-1 rounded border border-amber-500/40">
                    ▶ MultiTaskResNet18.layer4 Grad-CAM Heatmap ({currentCase.primaryVessel} Bottleneck)
                  </span>
                </div>
              </div>
            )}

            {selectedView === 'segmentation' && (
              <div className="relative w-full h-[360px] flex items-center justify-center">
                <Image
                  src={currentCase.maskUrl || rawScan}
                  alt={`Case ${currentCase.id} Artery Tree Prior`}
                  fill
                  className="object-contain"
                  unoptimized
                />
                <div className="absolute bottom-3 left-4 flex flex-col gap-1 pointer-events-none">
                  <span className="font-mono text-xs font-bold text-cyan-400 bg-slate-900/85 px-3 py-1 rounded border border-cyan-500/40">
                    Attention U-Net Vascular Prior (Dice: 68.33% · IoU: 53.56%)
                  </span>
                  <span className="font-mono text-[10px] text-slate-300 bg-slate-900/85 px-2 py-0.5 rounded">
                    Zhang-Suen Medial Centerline & Caliper Bounds
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Caliper Readout Footer */}
          <div className="p-3 bg-[#F8F9FA] border-t border-[#A91121]/15 flex items-center justify-between text-[11px] text-slate-600 font-mono flex-wrap gap-2">
            <span>Primary Lesion: <strong className="text-slate-900">{currentCase.primaryVessel}</strong></span>
            <span>%DS: <strong className="text-[#A91121] font-bold">{currentCase.maxStenosisPercent}%</strong></span>
            <span>MLD: <strong className="text-slate-900">{currentCase.mldMm?.toFixed(2) || '0.50'} mm</strong></span>
            <span>RVD: <strong className="text-slate-900">{currentCase.rvdMm?.toFixed(2) || '2.88'} mm</strong></span>
            <span>Lesion Length: <strong className="text-slate-900">{currentCase.lesionLengthMm?.toFixed(1) || '14.8'} mm</strong></span>
          </div>
        </div>

        {/* Case Properties & Notes Sidebar (1 col) */}
        <div className="space-y-6">
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-[#252525]">QCA Quantitative Calipers</h3>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Stenosis Severity</span>
                <StatusIndicator status={currentCase.severityCategory} />
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Diameter Stenosis (%DS)</span>
                <span className="font-mono font-bold text-[#A91121]">{currentCase.maxStenosisPercent}%</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Minimum Lumen (MLD)</span>
                <span className="font-mono font-semibold text-[#252525]">{currentCase.mldMm?.toFixed(2) || '0.50'} mm</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Reference Diameter (RVD)</span>
                <span className="font-mono font-semibold text-[#252525]">{currentCase.rvdMm?.toFixed(2) || '2.88'} mm</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Lesion Length</span>
                <span className="font-mono text-slate-700">{currentCase.lesionLengthMm?.toFixed(1) || '14.8'} mm</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">AHA Coronary Vessel</span>
                <span className="font-mono font-semibold text-[#A91121]">{currentCase.primaryVessel}</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Assigned Pipeline</span>
                <span className="font-mono text-xs text-slate-700">{currentCase.modelUsed}</span>
              </div>
            </div>
          </div>

          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-3">
            <h3 className="text-sm font-bold text-[#252525]">Clinical Guidance & Recommendation</h3>
            <div className="text-xs text-slate-700 bg-amber-50 border border-amber-200 p-3 rounded-lg leading-relaxed">
              <span className="font-bold text-amber-900 block mb-1">Hemodynamic Assessment:</span>
              {currentCase.recommendation || 'Fractional Flow Reserve (FFR/iFR) Evaluation Recommended prior to revascularization.'}
            </div>
            <p className="text-xs text-slate-600 bg-[#F5F5F5] p-3 rounded-lg border border-[#A91121]/20 font-sans leading-relaxed">
              {currentCase.notes}
            </p>
          </div>
        </div>
      </div>

      {/* Structured AI Explanation Summary Box */}
      <div className="bg-[#FAFBFD] border border-[#A91121]/20 rounded-xl p-5 space-y-4 shadow-xs text-left">
        <div className="flex items-center justify-between border-b border-[#A91121]/15 pb-3 flex-wrap gap-2">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center text-[#A91121]">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-[#252525]">AI Explanation Summary: Why Was This Region Flagged?</h4>
              <p className="text-[11px] text-slate-500">Visual attention attribution and feature contribution analysis</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded-md">
              Stenosis: Positive ({currentCase.severityCategory})
            </span>
            <span className="text-xs font-mono font-bold px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> 94.2% Calibrated Confidence
            </span>
          </div>
        </div>

        {/* Narrative Explanation Paragraph */}
        <div className="p-3.5 bg-white border border-[#A91121]/20 rounded-lg text-xs text-slate-700 leading-relaxed">
          <strong className="text-slate-900">Model Attribution & Visual Evidence: </strong>
          The model&apos;s attribution map demonstrates strong, localized activation concentrated along the mid-{currentCase.primaryVessel} coronary artery. This high-attribution zone overlaps directly with the segmented arterial lumen bottleneck, confirming that the prediction is driven by true intraluminal narrowing rather than surrounding bony ribs, diaphragm shadows, or catheter wires.
        </div>

        {/* 4 Feature Contribution Badges */}
        <div>
          <h5 className="text-xs font-bold text-slate-800 mb-2">Feature Contribution Analysis (What Influenced the Prediction):</h5>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div className="p-3 bg-white border border-[#A91121]/20 rounded-lg space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-800">Apparent Narrowing</span>
                <span className="font-mono font-bold text-[#A91121]">82.6%</span>
              </div>
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#A91121] h-full rounded-full" style={{ width: '82.6%' }} />
              </div>
              <p className="text-[11px] text-slate-500">Caliber drop from {currentCase.rvdMm?.toFixed(2) || '2.88'} to {currentCase.mldMm?.toFixed(2) || '0.50'} mm ({currentCase.maxStenosisPercent}% DS)</p>
            </div>

            <div className="p-3 bg-white border border-[#A91121]/20 rounded-lg space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-800">Boundary Step</span>
                <span className="font-mono font-bold text-amber-600">74.2%</span>
              </div>
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div className="bg-amber-500 h-full rounded-full" style={{ width: '74.2%' }} />
              </div>
              <p className="text-[11px] text-slate-500">Focal margin indentation and eccentric lumen step</p>
            </div>

            <div className="p-3 bg-white border border-[#A91121]/20 rounded-lg space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-800">Contrast Density</span>
                <span className="font-mono font-bold text-blue-600">68.9%</span>
              </div>
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div className="bg-blue-500 h-full rounded-full" style={{ width: '68.9%' }} />
              </div>
              <p className="text-[11px] text-slate-500">Radiopaque contrast dye density drop across core</p>
            </div>

            <div className="p-3 bg-white border border-[#A91121]/20 rounded-lg space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-800">Centerline Path</span>
                <span className="font-mono font-bold text-emerald-600">62.4%</span>
              </div>
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full rounded-full" style={{ width: '62.4%' }} />
              </div>
              <p className="text-[11px] text-slate-500">Geometric continuity along {currentCase.lesionLengthMm?.toFixed(1) || '14.8'} mm tract</p>
            </div>
          </div>
        </div>

        {/* Prediction Confidence & Limitations Card */}
        <div className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-lg flex items-start gap-2.5 text-xs text-amber-950">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold">Explanation Reliability & Clinical Disclaimer:</span>
            <p className="text-[11px] text-amber-900 leading-relaxed">
              Model attribution reflects deep neural network feature importance and must not be interpreted as histological proof. 2D projection foreshortening may slightly alter apparent tapering. All AI findings require verification by an interventional cardiologist before committing to invasive catheterization.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
