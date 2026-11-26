'use client';

import React from 'react';
import Image from 'next/image';
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Eye,
  FileBarChart2,
  Layers,
  Lock,
  ShieldCheck,
  Sparkles,
  Stethoscope,
} from 'lucide-react';

interface LandingPageProps {
  onEnterLogin: () => void;
}

const BENCHMARKS = [
  {
    value: '0.6833',
    label: 'Artery Dice Score',
    detail: 'Attention U-Net · 0.5356 IoU · 99.09% Specificity',
  },
  {
    value: '87.43%',
    label: 'Stenosis Detection Acc.',
    detail: 'Multi-Task ResNet-18 · 74.86% 4-Tier · 9.54% %DS MAE',
  },
  {
    value: '89.4%',
    label: 'Grad-CAM Focus Within Vessel',
    detail: 'Masked Grad-CAM on layer4 focused inside the vessel region',
  },
  {
    value: '33.94 FPS',
    label: 'Inference Speed',
    detail: 'RTX 2050 benchmark · < 500 ms PDF report generation',
  },
];

const PIPELINE_STAGES = [
  {
    step: '01',
    title: 'Preprocessing & Lumen Segmentation',
    desc: 'Applies CLAHE contrast enhancement on 2D XCA and HU-windowed 3D CCTA slices, then uses Attention U-Net with attention-based filtering to reduce catheter and rib interference.',
    icon: Layers,
  },
  {
    step: '02',
    title: 'Centerline, EDT & QCA %DS',
    desc: 'Uses Zhang-Suen Thinning and Euclidean Distance Transform (EDT) with proximal and distal reference measurements to calculate Minimal Lumen Diameter (MLD) and Percentage Diameter Stenosis (%DS) via Quantitative Coronary Angiography (QCA).',
    icon: Activity,
  },
  {
    step: '03',
    title: 'Lesion Detection & Severity Grading',
    desc: 'Detects lesions using vessel-region-filtered Faster R-CNN (MobileNetV3-FPN) with Soft-NMS and AHA Branch Mapping, followed by Multi-Task ResNet-18 severity classification.',
    icon: Cpu,
  },
  {
    step: '04',
    title: 'Grad-CAM & Clinical Reports',
    desc: 'Generates five-panel model explanation cards with Grad-CAM overlays, interactive lumen plots, and PDF, JSON, and CSV report generation.',
    icon: FileBarChart2,
  },
];

const ROLES = [
  {
    role: 'Radiologist / Clinician',
    scope: 'Upload 2D XCA / 3D CCTA scans, inspect QCA measurements and Grad-CAM cards, and review diagnostic reports.',
    icon: Stethoscope,
  },
  {
    role: 'Medical Researcher',
    scope: 'Review patient group severity statistics, export %DS datasets, and audit validation cases.',
    icon: Eye,
  },
  {
    role: 'Data Scientist',
    scope: 'Compare U-Net, Attention U-Net, and ResNet-18 benchmarks and track model performance monitoring.',
    icon: Sparkles,
  },
  {
    role: 'Administrator & Developer',
    scope: 'Manage Role-Based Access Control (RBAC) accounts, inspect login audit trails, monitor system health, and verify APIs.',
    icon: ShieldCheck,
  },
];

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterLogin }) => {
  return (
    <div className="min-h-screen bg-slate-50 text-[#252525] font-sans flex flex-col">
      {/* Top Navigation */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-slate-200/80">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 h-16 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Image
              src="/assets/stenovision_heartbeat_ribbon_logo.svg"
              alt="StenoVision Logo"
              width={150}
              height={48}
              unoptimized
              className="h-9 w-auto object-contain"
              priority
            />
          </div>

          <nav className="hidden md:flex items-center gap-7 text-xs font-semibold text-slate-600">
            <a href="#benchmarks" className="hover:text-[#A91121] transition-colors">
              Benchmarks
            </a>
            <a href="#pipeline" className="hover:text-[#A91121] transition-colors">
              AI Pipeline
            </a>
            <a href="#xai-preview" className="hover:text-[#A91121] transition-colors">
              Grad-CAM Preview
            </a>
            <a href="#roles" className="hover:text-[#A91121] transition-colors">
              Clinical Roles
            </a>
          </nav>

          <button
            type="button"
            onClick={onEnterLogin}
            className="px-4 py-2 bg-[#A91121] hover:bg-[#800D1B] text-white text-xs font-semibold rounded-xl shadow-sm shadow-[#A91121]/20 inline-flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <Lock className="w-3.5 h-3.5" />
            Sign In
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-white via-slate-50 to-slate-100/70 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 py-14 lg:py-20 grid lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-6 space-y-6">
            <h1 className="text-3xl sm:text-4xl lg:text-[42px] font-extrabold tracking-tight text-[#1c1c1c] leading-[1.14]">
              Automated Coronary Artery Segmentation &amp;{' '}
              <span className="text-[#A91121]">Stenosis Detection</span>
            </h1>

            <p className="text-sm sm:text-base text-slate-600 leading-relaxed max-w-xl">
              StenoVision combines coronary artery segmentation, stenosis detection, severity
              classification, and Grad-CAM visualization in a single platform with role-based
              access.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-1">
              <button
                type="button"
                onClick={onEnterLogin}
                className="px-6 py-3 bg-[#A91121] hover:bg-[#800D1B] text-white text-sm font-semibold rounded-xl shadow-lg shadow-[#A91121]/20 inline-flex items-center gap-2 transition-all cursor-pointer"
              >
                Sign In
                <ArrowRight className="w-4 h-4" />
              </button>
              <a
                href="#pipeline"
                className="px-5 py-3 bg-white hover:bg-slate-50 text-[#252525] text-sm font-semibold rounded-xl border border-slate-300 transition-colors"
              >
                Explore 4-Stage Pipeline
              </a>
            </div>
          </div>

          {/* Right XAI Visual Preview Card */}
          <div id="xai-preview" className="lg:col-span-6">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden">
              <div className="px-4 py-3 bg-[#1c1c1c] text-white flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  5-Panel Model Explanation &amp; Masked Grad-CAM Output
                </div>
                <span className="text-[11px] font-mono text-slate-300">CASE-10 · 2D XCA</span>
              </div>
              <div className="p-3 bg-slate-950">
                <Image
                  src="/assets/cases/10_5panel_detection.png"
                  alt="StenoVision 5-Panel Coronary Artery Segmentation and Grad-CAM Preview"
                  width={1200}
                  height={420}
                  unoptimized
                  className="w-full h-auto rounded-lg object-contain"
                  priority
                />
              </div>
              <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-600">
                <span className="font-medium">
                  Attention U-Net + Faster R-CNN + ResNet-18 + QCA %DS
                </span>
                <span className="font-mono text-[#A91121] font-semibold">
                  PDF · JSON · CSV Report Generation
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Verified Benchmarks Strip */}
      <section id="benchmarks" className="max-w-7xl mx-auto w-full px-5 sm:px-8 py-12">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {BENCHMARKS.map((item) => (
            <div
              key={item.label}
              className="bg-white rounded-2xl border border-slate-200 border-l-4 border-l-[#A91121] p-5 shadow-sm"
            >
              <div className="text-2xl sm:text-3xl font-extrabold text-[#1c1c1c] tracking-tight">
                {item.value}
              </div>
              <div className="text-xs font-bold uppercase tracking-wider text-[#A91121] mt-1">
                {item.label}
              </div>
              <p className="text-xs text-slate-500 mt-2 leading-relaxed">{item.detail}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 4-Stage Deep Learning Pipeline */}
      <section id="pipeline" className="max-w-7xl mx-auto w-full px-5 sm:px-8 py-8 pb-14">
        <div className="max-w-2xl mb-8">
          <h2 className="text-2xl font-bold text-[#1c1c1c]">Four-Stage Analysis Pipeline</h2>
          <p className="text-sm text-slate-600 mt-1.5">
            Our system follows four stages to segment coronary arteries, detect stenosis, measure
            narrowing, and generate visual explanations.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-5">
          {PIPELINE_STAGES.map((stage) => {
            const Icon = stage.icon;
            return (
              <div
                key={stage.step}
                className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:border-[#A91121]/40 transition-colors"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-xl bg-red-50 text-[#A91121] flex items-center justify-center shrink-0">
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-bold uppercase tracking-widest text-slate-400">
                      Stage {stage.step}
                    </span>
                    <h3 className="text-base font-bold text-[#1c1c1c]">{stage.title}</h3>
                  </div>
                </div>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">{stage.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Role-Based Clinical Access */}
      <section id="roles" className="bg-white border-y border-slate-200 py-14">
        <div className="max-w-7xl mx-auto px-5 sm:px-8">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
            <div>
              <h2 className="text-2xl font-bold text-[#1c1c1c]">Role-Based Clinical Access</h2>
              <p className="text-sm text-slate-600 mt-1">
                Role-based permissions across clinical review, research evaluation, and system
                management.
              </p>
            </div>
            <button
              type="button"
              onClick={onEnterLogin}
              className="px-4 py-2.5 bg-[#A91121] hover:bg-[#800D1B] text-white text-xs font-semibold rounded-xl inline-flex items-center gap-1.5 self-start sm:self-auto cursor-pointer"
            >
              Sign In with Demo Role
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {ROLES.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.role}
                  className="rounded-2xl border border-slate-200 bg-slate-50/70 p-5 space-y-2.5"
                >
                  <div className="w-9 h-9 rounded-lg bg-white border border-slate-200 text-[#A91121] flex items-center justify-center">
                    <Icon className="w-4 h-4" />
                  </div>
                  <h3 className="text-sm font-bold text-[#1c1c1c]">{item.role}</h3>
                  <p className="text-xs text-slate-600 leading-relaxed">{item.scope}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto bg-white border-t border-slate-200 text-slate-600 py-8">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs">
          <div>
            <p className="font-semibold text-[#1c1c1c]">
              StenoVision · Artery Segmentation &amp; Stenosis Detection System
            </p>
            <p className="text-slate-500 mt-0.5">
              Infosys Springboard Virtual Internship 7.0 · Team No. 1
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-5 text-slate-600 font-medium">
            <a href="#benchmarks" className="hover:text-[#A91121] transition-colors">
              Benchmarks
            </a>
            <a href="#pipeline" className="hover:text-[#A91121] transition-colors">
              AI Pipeline
            </a>
            <a href="#explainability" className="hover:text-[#A91121] transition-colors">
              Grad-CAM Preview
            </a>
            <a href="#roles" className="hover:text-[#A91121] transition-colors">
              Clinical Roles
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};
