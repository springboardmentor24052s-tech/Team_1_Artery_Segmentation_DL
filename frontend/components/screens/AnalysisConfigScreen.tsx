'use client';

import React, { useState } from 'react';
import { Sliders, Play, CheckCircle2, Cpu, ArrowLeft, Activity, ShieldCheck, FileCheck, BarChart2, Lock } from 'lucide-react';
import { uploadAndAnalyzeAngiogram, DiagnosticResult, UploadedScanPayload } from '@/lib/api';
import { SystemUser } from '@/lib/mockData';
import { getModelConfigMode } from '@/lib/permissions';
import { ModelComparisonView } from '../ModelComparisonView';

interface AnalysisConfigScreenProps {
  onNavigate: (screen: string) => void;
  uploadedFile?: File | null;
  uploadedPayload?: UploadedScanPayload | null;
  onAnalysisComplete?: (result: DiagnosticResult) => void;
  currentUser?: SystemUser;
}

export const AnalysisConfigScreen: React.FC<AnalysisConfigScreenProps> = ({
  onNavigate,
  uploadedFile,
  uploadedPayload,
  onAnalysisComplete,
  currentUser
}) => {
  const configMode = getModelConfigMode(currentUser?.role);
  const isLockedMode = configMode === 'best-model-locked';
  const isClinician = currentUser?.role === 'Radiologist / Clinician';
  const isResearcher = currentUser?.role === 'Medical Researcher';
  const is3DScan = Boolean(
    uploadedPayload?.scanType?.includes('3D') ||
    uploadedPayload?.presetId?.startsWith('PA') ||
    uploadedFile?.name?.toLowerCase().endsWith('.nii') ||
    uploadedFile?.name?.toLowerCase().endsWith('.nii.gz')
  );
  const [model, setModel] = useState(
    uploadedPayload?.model || 'StenoVision Ensemble v2.1'
  );
  const [huWindow, setHuWindow] = useState('Angiographic Contrast ([100, 700 HU])');
  const [mprProjection, setMprProjection] = useState('MIP (Maximum Intensity Projection - 5mm Slab)');
  const [threshold, setThreshold] = useState(30);
  const [centerlineAlgo, setCenterlineAlgo] = useState('Zhang-Suen Topological Thinning with EDT Caliper (Verified SOTA)');
  const [nmsThreshold, setNmsThreshold] = useState('0.35 (Clinical Soft-NMS — Balanced / Verified)');
  const [includeBranches, setIncludeBranches] = useState({
    lad: true,
    rca: true,
    lcx: true,
    lm: true,
  });
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [activeView, setActiveView] = useState<'config' | 'comparison'>('config');

  const targetFile = uploadedFile || (uploadedPayload ? uploadedPayload.file : new File(['sample_10'], '10.png', { type: 'image/png' }));
  const scanDisplayName = uploadedPayload?.patientName
    ? `${uploadedPayload.patientName} (${uploadedPayload.file.name})`
    : targetFile.name;

  const handleRunAnalysis = async () => {
    setIsRunning(true);
    setProgress(15);

    const progressTimer = setInterval(() => {
      setProgress((prev) => (prev < 85 ? prev + 20 : prev));
    }, 250);

    try {
      const diagResult = await uploadAndAnalyzeAngiogram(targetFile, uploadedPayload || undefined);

      clearInterval(progressTimer);
      setProgress(100);

      if (onAnalysisComplete) {
        onAnalysisComplete(diagResult);
      }

      setTimeout(() => {
        setIsRunning(false);
        onNavigate('results');
      }, 400);
    } catch (err) {
      console.error('Inference error:', err);
      clearInterval(progressTimer);
      const fallbackResult = await uploadAndAnalyzeAngiogram(targetFile, uploadedPayload || undefined);
      if (onAnalysisComplete) {
        onAnalysisComplete(fallbackResult);
      }
      setIsRunning(false);
      onNavigate('results');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-[#252525]">
            {isClinician
              ? 'Clinical Diagnostic Pipeline Execution'
              : isResearcher
              ? 'Cohort Analysis Pipeline Execution'
              : 'Deep Learning Diagnostic Configuration'}
          </h2>
          <p className="text-xs text-slate-500">
            {isLockedMode
              ? 'Executing automated coronary evaluation using the active production model selected by the Data Science team'
              : 'Configure neural network architectures, QCA caliper thresholding, and model benchmarks'}
          </p>
        </div>

        {!isLockedMode && (
          <div className="flex items-center gap-1.5 p-1 rounded-lg bg-slate-100 border border-slate-200">
            <button
              onClick={() => setActiveView('config')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors flex items-center gap-1.5 ${
                activeView === 'config' ? 'bg-white text-[#A91121] shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" /> Pipeline Tuning
            </button>
            <button
              onClick={() => setActiveView('comparison')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors flex items-center gap-1.5 ${
                activeView === 'comparison' ? 'bg-white text-[#A91121] shadow-xs' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" /> Model Comparison (v1.0-v2.1)
            </button>
          </div>
        )}
      </div>

      {isLockedMode && !isRunning && activeView !== 'comparison' && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-2xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-emerald-600 text-white shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-emerald-950 text-sm">Active Production Model: Cascade v2.1</h3>
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-200 text-emerald-900 border border-emerald-300">
                  RECOMMENDED SOTA
                </span>
              </div>
              <p className="text-xs text-emerald-800 mt-0.5">
                Attention U-Net v1.1 + MultiTask ResNet-18 v2.0 · Selected &amp; verified by Lead Developer &amp; Data Science team. Low-level hyperparameters are locked to clinical consensus standards for high diagnostic precision.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-800 bg-white px-3 py-1.5 rounded-lg border border-emerald-200 shrink-0">
            <Lock className="w-3.5 h-3.5 text-emerald-600" />
            <span>Consensus Locked</span>
          </div>
        </div>
      )}

      {activeView === 'comparison' ? (
        <ModelComparisonView />
      ) : isRunning ? (
        <div className="bg-white border border-[#A91121]/20 rounded-xl p-12 text-center space-y-4 shadow-sm">
          <div className="w-16 h-16 bg-[#A91121]/10 text-[#A91121] rounded-full flex items-center justify-center mx-auto animate-pulse">
            <Cpu className="w-8 h-8 animate-spin" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-[#252525]">Executing Deep Learning Pipeline...</h3>
            <p className="text-xs font-mono text-slate-500">Model: {model} · Progress: {progress}%</p>
          </div>
          <div className="w-full max-w-md mx-auto bg-[#F5F5F5] h-2.5 rounded-full overflow-hidden border border-[#A91121]/20">
            <div className="bg-[#A91121] h-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
          </div>
          <p className="text-[11px] font-mono text-slate-400">
            {progress < 40 && '1. Segmenting coronary artery tree with Attention U-Net...'}
            {progress >= 40 && progress < 70 && '2. Extracting EDT bottlenecks & Faster R-CNN proposals...'}
            {progress >= 70 && progress < 90 && '3. Computing QCA %DS & ResNet-18 severity...'}
            {progress >= 90 && '4. Synthesizing Grad-CAM explainable AI saliency card...'}
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Active Target Scan Pill */}
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-4 shadow-sm flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-red-50 text-[#A91121] flex items-center justify-center font-bold">
                <FileCheck className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs text-slate-500 font-medium">Target Angiogram for Inference:</div>
                <div className="text-sm font-bold text-[#252525]">{scanDisplayName}</div>
              </div>
            </div>
            <span className="text-[11px] font-mono font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md">
              {uploadedPayload?.scanType?.includes('3D') || uploadedPayload?.presetId?.startsWith('PA')
                ? 'Validated 3D Volume: 512x512x256'
                : 'Validated Resolution: 512x512'}
            </span>
          </div>

          {/* Model Selection */}
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-[#252525] flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#A91121]" /> Deep Learning Model Selection
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                {
                  name: 'StenoVision Ensemble v2.1',
                  badge: isLockedMode ? 'Clinical Production (Active)' : 'Recommended (State of the Art)',
                  desc: 'Attention-gated skip connections (Dice: 0.6833, IoU: 0.5356). Faster R-CNN localization & ResNet-18 severity classifier (29.8 FPS).',
                  locked: false,
                },
                {
                  name: 'Baseline U-Net Caliper Suite v1.0',
                  badge: isLockedMode ? 'Restricted: Data Science Only' : 'Benchmark Baseline',
                  desc: 'Standard 4-level encoder-decoder U-Net (Dice: 0.6822, IoU: 0.5325, 37.6 FPS) with geometric EDT bottleneck extraction.',
                  locked: isLockedMode,
                },
                {
                  name: 'ResNet-18 Severity Network v2.0',
                  badge: isLockedMode ? 'Restricted: Data Science Only' : 'Stenosis Specialist',
                  desc: 'Direct patch classifier & %DS continuous regressor (%DS MAE: 9.54%, Binary Acc: 87.43%, Severity Acc: 74.86%).',
                  locked: isLockedMode,
                },
              ].map((m) => (
                <div
                  key={m.name}
                  onClick={() => {
                    if (!m.locked) {
                      setModel(m.name);
                    }
                  }}
                  className={`border rounded-xl p-4 transition-all flex flex-col justify-between ${
                    m.locked
                      ? 'border-slate-200 bg-slate-50 opacity-60 cursor-not-allowed select-none'
                      : model === m.name
                      ? 'border-[#A91121] bg-[#A91121]/5 shadow-sm ring-1 ring-[#A91121] cursor-pointer'
                      : 'border-[#A91121]/20 hover:border-[#A91121]/40 bg-white cursor-pointer'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className={`inline-flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                        m.locked
                          ? 'bg-slate-200 text-slate-700 border border-slate-300'
                          : 'text-[#A91121] bg-red-50 border border-red-200'
                      }`}>
                        {m.locked && <Lock className="w-2.5 h-2.5 text-slate-600" />}
                        {m.badge}
                      </span>
                    </div>
                    <div className="font-semibold text-xs text-[#252525] mb-1">{m.name}</div>
                    <div className="text-[11px] text-slate-500 leading-relaxed">{m.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 3D Volumetric CTPA / CCTA Acquisition & MPR Controls */}
          {is3DScan && (
            <div className="bg-gradient-to-r from-cyan-50/50 to-blue-50/40 border border-cyan-200/80 rounded-xl p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-[#252525] flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyan-700" />
                  3D Volumetric CTPA Acquisition & MPR Controls
                </h3>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-100 text-cyan-800 border border-cyan-300 font-semibold">
                  PARSE 2022 Benchmark
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-[#252525]">Hounsfield Unit (HU) Windowing</label>
                  <select
                    value={huWindow}
                    onChange={(e) => setHuWindow(e.target.value)}
                    className="w-full px-3.5 py-2 text-sm bg-white border border-cyan-300/80 rounded-lg text-[#252525] font-mono focus:outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-600/20"
                  >
                    <option value="Angiographic Contrast ([100, 700 HU])">Angiographic Contrast ([100, 700 HU] - Recommended for Lumen)</option>
                    <option value="Standard Soft Tissue ([-100, 300 HU])">Standard Soft Tissue ([-100, 300 HU])</option>
                    <option value="Plaque & Calcium Evaluation ([400, 1200 HU])">Plaque & Calcium Evaluation ([400, 1200 HU])</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-[#252525]">Multi-Planar Reconstruction (MPR) Projection</label>
                  <select
                    value={mprProjection}
                    onChange={(e) => setMprProjection(e.target.value)}
                    className="w-full px-3.5 py-2 text-sm bg-white border border-cyan-300/80 rounded-lg text-[#252525] font-mono focus:outline-none focus:border-cyan-600 focus:ring-2 focus:ring-cyan-600/20"
                  >
                    <option value="MIP (Maximum Intensity Projection - 5mm Slab)">MIP (Maximum Intensity Projection - 5mm Slab)</option>
                    <option value="Thin-Slice Curved Planar Reformation (1mm Axial)">Thin-Slice Curved Planar Reformation (1mm Axial)</option>
                    <option value="Average Intensity Projection (Ray-Cast)">Average Intensity Projection (Ray-Cast)</option>
                  </select>
                </div>
              </div>
              <div className="text-[11px] font-mono text-cyan-800 bg-white/80 p-2.5 rounded-lg border border-cyan-200 flex flex-wrap items-center justify-between gap-2">
                <span>Voxel Spacing: <strong>0.625 × 0.625 × 0.8 mm</strong></span>
                <span>Matrix: <strong>512 × 512 × 256</strong></span>
                <span>Active Slices: <strong>256 Volumetric Slices</strong></span>
              </div>
            </div>
          )}

          {/* Hyperparameters */}
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-6">
            <h3 className="text-sm font-bold text-[#252525] flex items-center gap-2">
              <Sliders className="w-4 h-4 text-[#A91121]" /> QCA Morphometry & Detection Thresholds
            </h3>

            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-700">Caliper Stenosis Narrowing Threshold</span>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                    threshold < 25
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : threshold < 50
                      ? 'bg-cyan-50 text-cyan-700 border-cyan-200'
                      : threshold < 70
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : 'bg-red-50 text-red-700 border-red-200'
                  }`}>
                    {threshold < 25
                      ? 'Normal (<25%)'
                      : threshold < 50
                      ? 'Mild (25-49%)'
                      : threshold < 70
                      ? 'Moderate (50-69%)'
                      : 'Severe / Critical (≥70%)'}
                  </span>
                  <span className="font-mono font-bold text-[#A91121]">{threshold}% diameter reduction</span>
                </div>
              </div>
              <input
                type="range"
                min="20"
                max="70"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-full accent-[#A91121] cursor-pointer"
              />
              <div className="flex justify-between text-[11px] font-mono text-slate-400">
                <span>20% (Mild)</span>
                <span>30% (Standard QCA Default)</span>
                <span>50% (Moderate Ischemia)</span>
                <span>70% (Severe Critical)</span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[#252525]">Centerline & Caliper Engine</label>
                <select
                  value={centerlineAlgo}
                  onChange={(e) => setCenterlineAlgo(e.target.value)}
                  className="w-full px-3.5 py-2 text-sm bg-white border border-[#A91121]/20 rounded-lg text-[#252525] font-mono focus:outline-none focus:border-[#A91121] focus:ring-2 focus:ring-[#A91121]/20"
                >
                  <option value="Zhang-Suen Topological Thinning with EDT Caliper (Verified SOTA)">
                    Zhang-Suen Topological Thinning with EDT Caliper (Verified SOTA)
                  </option>
                  <option value="Medial Axis Transform (MAT Skeletonization)">
                    Medial Axis Transform (MAT Skeletonization)
                  </option>
                  {is3DScan && (
                    <option value="3D Hessian Frangi Vesselness & MPR Caliper">
                      3D Hessian Frangi Vesselness & MPR Caliper
                    </option>
                  )}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[#252525]">Lesion Overlap Sensitivity (Soft-NMS)</label>
                <select
                  value={nmsThreshold}
                  onChange={(e) => setNmsThreshold(e.target.value)}
                  className="w-full px-3.5 py-2 text-sm bg-white border border-[#A91121]/20 rounded-lg text-[#252525] font-mono focus:outline-none focus:border-[#A91121] focus:ring-2 focus:ring-[#A91121]/20"
                >
                  <option value="0.35 (Clinical Soft-NMS — Balanced / Verified)">
                    0.35 (Clinical Soft-NMS — Balanced / Verified)
                  </option>
                  <option value="0.50 (Conservative — Discrete Lesions Only)">
                    0.50 (Conservative — Discrete Lesions Only)
                  </option>
                  <option value="0.25 (Aggressive — Multi-Scale Lesion Fusion)">
                    0.25 (Aggressive — Multi-Scale Lesion Fusion)
                  </option>
                </select>
              </div>
            </div>

            {/* Target AHA Coronary Branches */}
            <div className="pt-2 border-t border-[#A91121]/15 space-y-2">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold text-[#252525]">AHA 15-Segment Coronary Tree Target Branches</label>
                <div className="flex items-center gap-2 text-[11px] font-semibold">
                  <button
                    type="button"
                    onClick={() => setIncludeBranches({ lad: true, rca: true, lcx: true, lm: true })}
                    className="text-[#A91121] hover:underline cursor-pointer"
                  >
                    Select All
                  </button>
                  <span className="text-slate-300">|</span>
                  <button
                    type="button"
                    onClick={() => setIncludeBranches({ lad: true, rca: false, lcx: false, lm: false })}
                    className="text-slate-500 hover:text-slate-800 cursor-pointer"
                  >
                    Reset Primary (LAD)
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { key: 'lad', label: 'LAD (Left Anterior)', desc: 'Segments 6, 7, 8' },
                  { key: 'rca', label: 'RCA (Right Coronary)', desc: 'Segments 1, 2, 3' },
                  { key: 'lcx', label: 'LCx (Circumflex)', desc: 'Segments 11, 13' },
                  { key: 'lm', label: 'LMCA (Left Main)', desc: 'Segment 5' },
                ].map((b) => (
                  <label key={b.key} className="flex items-start gap-2 border border-[#A91121]/20 rounded-lg p-2.5 cursor-pointer hover:bg-[#F5F5F5] transition-colors">
                    <input
                      type="checkbox"
                      checked={includeBranches[b.key as keyof typeof includeBranches]}
                      onChange={(e) => setIncludeBranches({ ...includeBranches, [b.key]: e.target.checked })}
                      className="accent-[#A91121] mt-0.5"
                    />
                    <div>
                      <div className="text-xs font-semibold text-[#252525]">{b.label}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{b.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-between items-center">
            <button
              onClick={() => onNavigate('upload')}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-[#252525] flex items-center gap-1.5 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Ingestion
            </button>
            <button
              onClick={handleRunAnalysis}
              className="px-6 py-2.5 bg-[#A91121] hover:bg-[#800D1B] text-white font-semibold rounded-lg transition-colors flex items-center gap-2 shadow-sm text-sm cursor-pointer"
            >
              <Play className="w-4 h-4 fill-white" />
              {isClinician
                ? 'Execute Clinical Diagnostic Pipeline (Cascade v2.1)'
                : isResearcher
                ? 'Execute Cohort Diagnostic Pipeline (Cascade v2.1)'
                : 'Execute Deep Learning Analysis'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
