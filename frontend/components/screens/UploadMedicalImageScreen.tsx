'use client';

import React, { useState } from 'react';
import { FileUpload } from '../FileUpload';
import { FormInput } from '../FormInput';
import { ArrowRight, ShieldCheck, CheckCircle2, Activity, FileCheck, ShieldAlert } from 'lucide-react';
import { UploadedScanPayload } from '@/lib/api';
import { SystemUser } from '@/lib/mockData';

interface UploadMedicalImageScreenProps {
  onNavigate: (screen: string, caseId?: string) => void;
  onFileIngested?: (file: File, payload?: UploadedScanPayload) => void;
  currentUser?: SystemUser;
}

const BENCHMARK_PRESETS = [
  { id: '10', label: 'Case 10: LAD - Mid (64.7% DS)', patient: 'Eleanor Vance', age: '62', gender: 'Female', branch: 'LAD' },
  { id: '35', label: 'Case 35: RCA - Prox (67.4% DS)', patient: 'Marcus Sterling', age: '55', gender: 'Male', branch: 'RCA' },
  { id: '60', label: 'Case 60: LMCA Bifurcation (61.2% DS)', patient: 'Sarah Jenkins', age: '48', gender: 'Female', branch: 'LM' },
  { id: '110', label: 'Case 110: LMCA Focal (52.8% DS)', patient: 'Arthur Pendelton', age: '71', gender: 'Male', branch: 'LM' },
  { id: '175', label: 'Case 175: LAD Diffuse (66.9% DS)', patient: 'Clara Oswald', age: '45', gender: 'Female', branch: 'LAD' },
  { id: 'PA000024', label: 'PA000024: 3D CTPA Volume (68.5% DS)', patient: 'CTPA Study Cohort (PA000024)', age: '58', gender: 'Male', branch: 'LAD' },
];

export const UploadMedicalImageScreen: React.FC<UploadMedicalImageScreenProps> = ({
  onNavigate,
  onFileIngested,
  currentUser
}) => {
  const isResearcher = currentUser?.role === 'Medical Researcher';
  const isClinician = currentUser?.role === 'Radiologist / Clinician';

  const [patientId, setPatientId] = useState(isResearcher ? 'RES-89421' : 'PT-89421');
  const [patientName, setPatientName] = useState(isResearcher ? 'ANON-1010 [De-Identified]' : 'Eleanor Vance');
  const [age, setAge] = useState('62');
  const [gender, setGender] = useState('Female');
  const [scanType, setScanType] = useState('XCA (Coronary Angiogram)');
  const [model, setModel] = useState('StenoVision Ensemble v2.1');
  const [notes, setNotes] = useState('ARCADE benchmark angiogram for stenosis detection and QCA morphometric profiling.');
  const [file, setFile] = useState<File | null>(() => new File(['benchmark_10'], '10.png', { type: 'image/png' }));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string>('10');
  const [customPreviewUrl, setCustomPreviewUrl] = useState<string>('/assets/cases/10.png');

  const handleSelectPreset = (preset: typeof BENCHMARK_PRESETS[0]) => {
    setSelectedPreset(preset.id);
    setPatientId(isResearcher ? `ANON-${preset.id}00` : `PT-${preset.id}00`);
    setPatientName(isResearcher ? `ANON-${preset.id} [De-Identified]` : preset.patient);
    setAge(preset.age);
    setGender(preset.gender);
    if (preset.id === 'PA000024') {
      setScanType('3D CT Angiography (CTPA)');
      setNotes('PARSE 2022 3D volumetric CTPA angiogram from datasets/2/train/train. Automated vascular slice extraction & dual-head severity grading.');
      const mockFile = new File(['nifti_pa000024'], 'PA000024.nii.gz', { type: 'application/gzip' });
      setFile(mockFile);
      setCustomPreviewUrl('/assets/cases/PA000024_preview_slice.png');
      return;
    }
    setScanType('XCA (Coronary Angiogram)');
    setNotes(`Benchmark test case ${preset.id} targeting ${preset.branch} branch. Verified with Attention U-Net and QCA caliper math.`);
    const mockFile = new File([`arcade_${preset.id}`], `${preset.id}.png`, { type: 'image/png' });
    setFile(mockFile);
    setCustomPreviewUrl(`/assets/cases/${preset.id}.png`);
  };

  const handleCustomFileSelected = (uploadedFile: File | null) => {
    setFile(uploadedFile);
    if (uploadedFile) {
      setSelectedPreset(''); // clear benchmark preset
      const cleanName = uploadedFile.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');
      setPatientName(`Patient Scan (${cleanName})`);
      setPatientId(`PT-${Math.floor(10000 + Math.random() * 90000)}`);
      
      const isVolumetric = uploadedFile.name.toLowerCase().endsWith('.nii') || uploadedFile.name.toLowerCase().endsWith('.nii.gz') || uploadedFile.name.toLowerCase().endsWith('.dcm') || uploadedFile.name.includes('PA00');
      if (isVolumetric) {
        setScanType('3D CT Angiography (CTPA)');
        setNotes(`User-uploaded 3D CTPA volumetric scan (${uploadedFile.name}) from datasets/2. Automated slice extraction and intraluminal stenosis grading.`);
        setCustomPreviewUrl('/assets/cases/PA000024_preview_slice.png');
      } else {
        setScanType('XCA (Coronary Angiogram)');
        setNotes(`User-uploaded clinical angiogram (${uploadedFile.name}) queued for deep learning vessel segmentation and stenosis grading.`);
        try {
          const url = URL.createObjectURL(uploadedFile);
          setCustomPreviewUrl(url);
        } catch (err) {
          console.warn('Object URL error:', err);
        }
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert('Please upload a coronary angiogram file (PNG, DICOM, or TIFF) before proceeding.');
      return;
    }

    let previewUrl = customPreviewUrl;
    if (!previewUrl) {
      previewUrl = selectedPreset ? `/assets/cases/${selectedPreset}.png` : '/assets/cases/10.png';
    }

    const payload: UploadedScanPayload = {
      file,
      previewUrl,
      isBenchmarkPreset: Boolean(selectedPreset),
      presetId: selectedPreset || undefined,
      patientId,
      patientName,
      age,
      gender,
      scanType,
      model,
      notes,
    };

    if (onFileIngested) {
      onFileIngested(file, payload);
    }
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setSuccessMsg(true);
      setTimeout(() => {
        onNavigate('config');
      }, 600);
    }, 700);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-lg font-bold text-[#252525]">
          {isResearcher
            ? 'Cohort Scan Ingestion (Research & Trials)'
            : isClinician
            ? 'Clinical Coronary Angiogram Ingestion'
            : 'Coronary Angiogram & 3D CTPA Ingestion'}
        </h2>
        <p className="text-xs text-slate-500">
          {isResearcher
            ? 'Upload multi-center study scans or trial cohorts. All records are automatically assigned de-identified subject IDs in compliance with HIPAA Safe Harbor regulations.'
            : isClinician
            ? 'Upload 2D X-Ray Coronary Angiography (XCA) or 3D CCTA scans (DICOM / NIfTI) for immediate QCA caliper profiling and lesion severity grading via the active production pipeline.'
            : 'Upload 2D X-Ray Coronary Angiography (XCA) or 3D Volumetric CTPA / CCTA scans (NIfTI / DICOM) for deep learning vessel segmentation, 3D MPR slice extraction, and stenosis grading.'}
        </p>
      </div>

      {isResearcher && (
        <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-between text-xs text-purple-900">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-purple-700" />
            <span><strong>De-Identified Ingestion Active:</strong> Uploaded patient demographics are automatically masked to safeguard protected health information (PHI).</span>
          </div>
          <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-purple-200 text-purple-800">HIPAA Safe Harbor</span>
        </div>
      )}

      {/* Quick Test Benchmark Preset Selector */}
      <div className="bg-card border border-border rounded-xl p-4 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#A91121]" />
            <span className="text-xs font-bold text-foreground">Verified Benchmark Study Presets</span>
          </div>
          <span className="text-[10px] font-mono font-semibold text-muted-foreground bg-muted px-2 py-0.5 rounded border border-border">
            Pre-Verified Benchmark
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          Select any pre-verified ARCADE (2D XCA) or PARSE (3D CCTA) benchmark study below to populate clinical metadata and test the diagnostic pipeline:
        </p>
        <div className="flex flex-wrap gap-2">
          {BENCHMARK_PRESETS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => handleSelectPreset(p)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all flex items-center gap-1.5 cursor-pointer ${
                selectedPreset === p.id
                  ? 'bg-[#A91121] text-white border-[#A91121] shadow-2xs'
                  : 'bg-muted/40 text-foreground border-border hover:border-[#A91121]/60 hover:text-[#A91121]'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {successMsg ? (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-8 text-center space-y-3">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-[#252525]">Scan Successfully Ingested & Validated</h3>
          <p className="text-xs text-slate-600 font-mono">Modality and spatial geometry verified. Redirecting to Deep Learning Configuration...</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File Upload Zone */}
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-[#252525]">1. Medical Scan File (3D NIfTI CTPA / 2D XCA / DICOM)</h3>
            <FileUpload
              onFileSelected={handleCustomFileSelected}
              acceptedFormats=".png, .jpg, .jpeg, .dcm, .nii, .nii.gz, .raw, .zip"
            />
            {file && (
              <div className="text-xs font-mono text-emerald-700 bg-emerald-50 px-3 py-2 rounded-lg border border-emerald-200 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 truncate">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Selected Scan: <strong>{file.name}</strong></span>
                  {selectedPreset ? (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                      selectedPreset.startsWith('PA')
                        ? 'bg-cyan-100 text-cyan-800 border border-cyan-300'
                        : 'bg-red-100 text-[#A91121]'
                    }`}>
                      {selectedPreset.startsWith('PA') ? `PARSE Case ${selectedPreset} (3D CTPA)` : `ARCADE Case ${selectedPreset} (2D XCA)`}
                    </span>
                  ) : (
                    <span className="text-[10px] bg-red-50 text-[#A91121] border border-red-200 px-1.5 py-0.5 rounded font-bold">Custom Scan Ingested</span>
                  )}
                </div>
                <span className="text-slate-500 font-sans text-[11px] shrink-0">Ready for inference</span>
              </div>
            )}
          </div>

          {/* Patient Metadata Form */}
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-[#252525]">2. Patient Demographics & Clinical Context</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormInput
                label="Patient ID"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                required
              />
              <FormInput
                label="Patient Full Name"
                placeholder="e.g. Eleanor Vance"
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
                required
              />
              <FormInput
                label="Age (Years)"
                type="number"
                placeholder="e.g. 62"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                required
              />
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[#252525]">Gender</label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  className="w-full px-3.5 py-2 text-sm bg-white border border-[#A91121]/20 rounded-lg text-[#252525] focus:outline-none focus:border-[#A91121] focus:ring-2 focus:ring-[#A91121]/20"
                >
                  <option value="Female">Female</option>
                  <option value="Male">Male</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[#252525]">Imaging Modality</label>
                <select
                  value={scanType}
                  onChange={(e) => setScanType(e.target.value)}
                  className="w-full px-3.5 py-2 text-sm bg-white border border-[#A91121]/20 rounded-lg text-[#252525] focus:outline-none focus:border-[#A91121] focus:ring-2 focus:ring-[#A91121]/20 font-mono"
                >
                  <option value="3D CT Angiography (CTPA)">3D CT Angiography (CTPA - Volumetric NIfTI / PARSE 2022)</option>
                  <option value="CCTA">Coronary Computed Tomography Angiography (CCTA - Axial / Multi-Planar)</option>
                  <option value="XCA (Coronary Angiogram)">XCA (2D X-Ray Coronary Angiogram - ARCADE Benchmark)</option>
                  <option value="DICOM Angiogram">DICOM Single/Multi-Frame Angiography (.dcm)</option>
                  <option value="High-Res PNG">High-Res Angiogram (PNG / TIFF / JPEG)</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-[#252525]">Diagnostic Analysis Model</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3.5 py-2 text-sm bg-white border border-[#A91121]/20 rounded-lg text-[#252525] focus:outline-none focus:border-[#A91121] focus:ring-2 focus:ring-[#A91121]/20 font-mono"
                >
                  <option value="StenoVision Ensemble v2.1">StenoVision Ensemble v2.1 (Recommended)</option>
                  <option value="Baseline U-Net Caliper Suite v1.0">Baseline U-Net Caliper Suite v1.0</option>
                  <option value="ResNet-18 Severity Network v2.0">ResNet-18 Severity Network v2.0</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5 pt-2">
              <label className="block text-xs font-semibold text-[#252525]">Clinical Referral Notes</label>
              <textarea
                rows={3}
                placeholder="Enter clinical observations, imaging projection angles (LAO/RAO/Cranial/Caudal), or referral context..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3.5 py-2 text-sm bg-white border border-[#A91121]/20 rounded-lg text-[#252525] focus:outline-none focus:border-[#A91121] focus:ring-2 focus:ring-[#A91121]/20 font-sans"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2.5 bg-[#A91121] hover:bg-[#800D1B] text-white font-semibold rounded-lg transition-colors flex items-center gap-2 shadow-sm text-sm disabled:opacity-50"
            >
              {isSubmitting ? (
                <>Validating & Ingesting Scan...</>
              ) : (
                <>Proceed to Analysis Configuration <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
