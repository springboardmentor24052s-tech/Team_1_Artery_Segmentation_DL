'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { fetchModels, fetchRadarComparison, deployModel } from '@/lib/api';
import { SystemUser } from '@/lib/mockData';
import { canDeployModels } from '@/lib/permissions';
import {
  Cpu,
  CheckCircle2,
  Layers,
  Activity,
  Zap,
  BarChart2,
  ShieldCheck,
  Flame,
  ArrowRight,
  TrendingUp,
  Sliders,
  Info,
  Target,
  LayoutGrid,
  Lightbulb,
  Clock
} from 'lucide-react';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
} from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

export interface RegisteredModel {
  id: string;
  version: string;
  name: string;
  category: string;
  architecture: string;
  backbone: string;
  parameters: string;
  weightsFile: string;
  weightsSizeMb: number;
  releaseMilestone: string;
  status: string;
  isActive: boolean;
  dice?: number;
  iou?: number;
  precision: number;
  recall: number;
  specificity: number;
  accuracy: number;
  latencyMs: number;
  throughputFps: number;
  dsMae?: number;
  severityAccuracy?: number;
  description: string;
  strengths: string[];
  weaknesses: string[];
}

export const REGISTERED_MODELS: RegisteredModel[] = [
  {
    id: 'MOD-100',
    version: 'v1.0',
    name: 'Baseline U-Net',
    category: 'Vessel Segmentation',
    architecture: '4-Level Encoder-Decoder (Convolutional Skips)',
    backbone: 'Vanilla DoubleConv Blocks',
    parameters: '31.03M',
    weightsFile: 'best_unet.pth',
    weightsSizeMb: 118.5,
    releaseMilestone: 'Baseline Benchmark v1.0',
    status: 'Standard Baseline',
    isActive: false,
    dice: 0.6822,
    iou: 0.5325,
    precision: 0.7325,
    recall: 0.6614,
    specificity: 0.9905,
    accuracy: 0.9842,
    latencyMs: 26.61,
    throughputFps: 37.57,
    description: 'Standard medical segmentation architecture. Establishes the clinical segmentation baseline with high raw inference speed.',
    strengths: ['High throughput (37.6 FPS)', 'Low VRAM footprint (180 MB)', 'Stable convergence'],
    weaknesses: ['Lower sensitivity on distal branching', 'Lacks spatial attention filtering']
  },
  {
    id: 'MOD-101',
    version: 'v1.1',
    name: 'Attention U-Net',
    category: 'Vessel Segmentation',
    architecture: 'Attention-Gated Skip Connections (AG-UNet)',
    backbone: 'Additive Soft-Attention Gates',
    parameters: '34.88M',
    weightsFile: 'best_attention_unet.pth',
    weightsSizeMb: 133.2,
    releaseMilestone: 'Primary Segmenter v1.1',
    status: 'Attention Segmenter',
    isActive: true,
    dice: 0.6833,
    iou: 0.5356,
    precision: 0.7340,
    recall: 0.6642,
    specificity: 0.9909,
    accuracy: 0.9856,
    latencyMs: 29.46,
    throughputFps: 33.94,
    description: 'Advanced attention-gated segmentation network. Selectively suppresses background artifacts while preserving micro-vasculature.',
    strengths: ['Highest vessel Dice (68.33%) & IoU (53.56%)', 'Preserves fine caliber vessel contours', 'Eliminates catheter noise'],
    weaknesses: ['Moderate latency overhead (+2.85 ms over v1.0)']
  },
  {
    id: 'MOD-200',
    version: 'v2.0',
    name: 'ResNet-18 Severity Network',
    category: 'Stenosis Classification & Grading',
    architecture: 'Dual-Head ResNet-18 with Spatial Attention Pooling',
    backbone: 'Pretrained ResNet-18 + Custom Diagnostic Head',
    parameters: '11.24M',
    weightsFile: 'best_stenosis_classifier.pth',
    weightsSizeMb: 44.7,
    releaseMilestone: 'Severity Network v2.0',
    status: 'Diagnostic Classifier',
    isActive: true,
    precision: 0.8812,
    recall: 0.8654,
    specificity: 0.8920,
    accuracy: 0.8743,
    latencyMs: 14.20,
    throughputFps: 70.42,
    dsMae: 9.54,
    severityAccuracy: 0.7486,
    description: 'Specialized deep learning diagnostic head. Performs simultaneous binary presence classification, 4-tier ACC/AHA severity classification, and continuous %DS caliber regression.',
    strengths: ['Sub-10% MAE on %DS (9.54%)', 'Native Grad-CAM attribution hooks', '74.86% 4-tier clinical accuracy'],
    weaknesses: ['Requires region-of-interest candidate proposals']
  },
  {
    id: 'MOD-201',
    version: 'v2.1',
    name: 'StenoVision Hybrid Cascade',
    category: 'End-to-End Cascaded Pipeline',
    architecture: 'Attention U-Net + Faster R-CNN + ResNet-18 Classifier + EDT Caliper',
    backbone: 'Full Multi-Stage Architecture with Soft-NMS',
    parameters: '65.32M',
    weightsFile: 'ensemble_manifest.json',
    weightsSizeMb: 296.4,
    releaseMilestone: 'Cascade Release v2.1',
    status: 'Recommended Pipeline',
    isActive: true,
    dice: 0.6833,
    iou: 0.5356,
    precision: 0.8743,
    recall: 0.8520,
    specificity: 0.9909,
    accuracy: 0.8743,
    latencyMs: 33.55,
    throughputFps: 29.80,
    dsMae: 9.54,
    severityAccuracy: 0.7486,
    description: 'The recommended clinical system. Chains attention segmentation, morphological thinning, whole-image candidate proposals, patch classification, and QCA caliper assessment.',
    strengths: ['Complete end-to-end automated clinical workflow', 'Real-time performance at 29.8 FPS (> 25 FPS standard)', 'Automated 4-panel visual proofs & reports'],
    weaknesses: ['Higher combined parameter footprint (65.3M)']
  }
];

interface ModelComparisonViewProps {
  currentUser?: SystemUser;
}

export const ModelComparisonView: React.FC<ModelComparisonViewProps> = ({ currentUser }) => {
  const [models, setModels] = useState<RegisteredModel[]>(REGISTERED_MODELS);
  const [selectedModelId, setSelectedModelId] = useState<string>('MOD-201');
  const [benchmarkCase, setBenchmarkCase] = useState<'10' | '35' | '110' | 'PA000042' | 'PA000024'>('10');
  const [activeTab, setActiveTab] = useState<'scorecard' | 'radar' | 'qualitative'>('scorecard');
  const [benchmarkMetric, setBenchmarkMetric] = useState<'accuracy' | 'dice' | 'iou' | 'speed' | 'params'>('accuracy');
  const [deployingId, setDeployingId] = useState<string | null>(null);

  useEffect(() => {
    async function loadModelsFromApi() {
      try {
        const fetched = await fetchModels();
        if (fetched && fetched.length > 0) {
          setModels(fetched);
        }
      } catch (e) {
        console.warn('Using default models registry.', e);
      }
    }
    loadModelsFromApi();
  }, []);

  const selectedModel = models.find((m) => m.id === selectedModelId) || models[3];

  // Computed KPI metrics from live registered models
  const totalVersions = models.length;
  const classificationModel = models.find((m) => m.id === 'MOD-200') || models.find((m) => m.category.includes('Classification'));
  const bestClassificationAccuracy = classificationModel ? classificationModel.accuracy : 0.8743;
  const fastestSpeed = Math.max(...models.map((m) => m.throughputFps));
  const recommendedModel = models.find((m) => m.id === 'MOD-201') || models[3];

  // Dynamic benchmark bar chart calculations bound to live registered models
  const getBarData = (metric: 'accuracy' | 'dice' | 'iou' | 'speed' | 'params') => {
    switch (metric) {
      case 'accuracy':
        return {
          minY: 70,
          maxY: 100,
          yTicks: ['100%', '95%', '90%', '85%', '80%', '75%', '70%'],
          bars: models.map((m) => ({
            id: m.id,
            version: m.version,
            name: m.name,
            displayValue: `${(m.accuracy * 100).toFixed(1)}%`,
            heightPct: Math.max(15, Math.min(88, ((m.accuracy * 100 - 70) / (100 - 70)) * 88)),
            isPrimary: m.category.includes('Segmentation')
          })),
          footnote: 'v1.x report pixel accuracy (segmentation); v2.x report classification accuracy. They are not directly comparable.'
        };
      case 'dice':
        return {
          minY: 0,
          maxY: 100,
          yTicks: ['100%', '80%', '60%', '40%', '20%', '0%'],
          bars: models.map((m) => ({
            id: m.id,
            version: m.version,
            name: m.name,
            displayValue: m.id === 'MOD-200' ? 'Classifier Head' : (m.dice && m.dice > 0 ? `${(m.dice * 100).toFixed(2)}%` : 'N/A'),
            heightPct: m.dice && m.dice > 0 ? Math.min(88, m.dice * 88) : 4,
            isPrimary: m.category.includes('Segmentation')
          })),
          footnote: 'v1.x and v2.1 feature vessel segmentation; v2.0 is a specialized stenosis classifier focused on %DS caliber regression & ACC/AHA grading.'
        };
      case 'iou':
        return {
          minY: 0,
          maxY: 100,
          yTicks: ['100%', '80%', '60%', '40%', '20%', '0%'],
          bars: models.map((m) => ({
            id: m.id,
            version: m.version,
            name: m.name,
            displayValue: m.id === 'MOD-200' ? 'Classifier Head' : (m.iou && m.iou > 0 ? `${(m.iou * 100).toFixed(2)}%` : 'N/A'),
            heightPct: m.iou && m.iou > 0 ? Math.min(88, m.iou * 88) : 4,
            isPrimary: m.category.includes('Segmentation')
          })),
          footnote: 'Intersection-over-Union segmentation overlap metric on test coronary angiograms.'
        };
      case 'speed':
        return {
          minY: 0,
          maxY: 80,
          yTicks: ['80', '60', '40', '20', '0'],
          bars: models.map((m) => ({
            id: m.id,
            version: m.version,
            name: m.name,
            displayValue: `${m.throughputFps} FPS`,
            heightPct: Math.min(88, (m.throughputFps / 80) * 88),
            isPrimary: m.category.includes('Segmentation')
          })),
          footnote: 'Inference throughput in frames per second (FPS) on NVIDIA RTX GPU. All models exceed 25 FPS fluoroscopy standard.'
        };
      case 'params':
        return {
          minY: 0,
          maxY: 75,
          yTicks: ['75M', '60M', '45M', '30M', '15M', '0M'],
          bars: models.map((m) => {
            const num = parseFloat(m.parameters.replace('M', '')) || 0;
            return {
              id: m.id,
              version: m.version,
              name: m.name,
              displayValue: m.parameters,
              heightPct: Math.min(88, (num / 75) * 88),
              isPrimary: m.category.includes('Segmentation')
            };
          }),
          footnote: 'Total learnable parameter footprint in millions of weights (memory footprint).'
        };
    }
  };

  const handleDeploy = async (id: string) => {
    if (!canDeployModels(currentUser?.role)) {
      console.warn('Model deployment restricted to Developer and Data Scientist.');
      return;
    }
    setDeployingId(id);
    try {
      await deployModel(id, currentUser?.role);
      setModels((prev) =>
        prev.map((m) => {
          if (m.id === id) {
            return { ...m, isActive: true, status: 'Recommended Pipeline' };
          }
          if (m.category === 'End-to-End Cascaded Pipeline') {
            return { ...m, isActive: false, status: 'Standby Candidate' };
          }
          return m;
        })
      );
    } finally {
      setTimeout(() => setDeployingId(null), 500);
    }
  };

  // Radar Data
  const radarData = {
    labels: [
      'Segmentation Dice',
      'Stenosis Accuracy',
      'Throughput (FPS)',
      'Memory Efficiency',
      'Explainability (XAI)',
      'Boundary Specificity'
    ],
    datasets: [
      {
        label: 'v1.0 Baseline U-Net',
        data: [68.2, 50.0, 95.0, 85.0, 40.0, 99.0],
        backgroundColor: 'rgba(59, 130, 246, 0.15)',
        borderColor: '#3B82F6',
        pointBackgroundColor: '#3B82F6',
      },
      {
        label: 'v1.1 Attention U-Net',
        data: [68.3, 50.0, 88.0, 80.0, 65.0, 99.1],
        backgroundColor: 'rgba(16, 185, 129, 0.15)',
        borderColor: '#10B981',
        pointBackgroundColor: '#10B981',
      },
      {
        label: 'v2.0 ResNet-18 Severity Network',
        data: [0.0, 87.4, 100.0, 95.0, 92.0, 89.2],
        backgroundColor: 'rgba(245, 158, 11, 0.15)',
        borderColor: '#F59E0B',
        pointBackgroundColor: '#F59E0B',
      },
      {
        label: 'v2.1 StenoVision Cascade (Recommended)',
        data: [68.3, 87.4, 75.0, 70.0, 98.0, 99.1],
        backgroundColor: 'rgba(169, 17, 33, 0.25)',
        borderColor: '#A91121',
        pointBackgroundColor: '#A91121',
      }
    ]
  };

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        angleLines: { color: 'rgba(0, 0, 0, 0.1)' },
        suggestedMin: 0,
        suggestedMax: 100,
        ticks: { backdropColor: 'transparent', font: { size: 10 } }
      }
    },
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: { boxWidth: 12, font: { size: 11 } }
      }
    }
  };

  return (
    <div className="space-y-3">
      
      {/* 4 KPI Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-3">
        {/* Card 1: Model Versions */}
        <div className="p-2.5 sm:p-3 rounded-xl border border-border bg-card shadow-2xs flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#A91121]/10 text-[#A91121] shrink-0">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-foreground tracking-tight leading-none">
              {totalVersions}
            </div>
            <div className="text-[11px] font-semibold text-foreground mt-0.5">Model Versions</div>
            <div className="text-[10px] text-muted-foreground font-mono">
              ({models[0]?.version}–{models[models.length - 1]?.version})
            </div>
          </div>
        </div>

        {/* Card 2: Best Classification Accuracy */}
        <div className="p-2.5 sm:p-3 rounded-xl border border-border bg-card shadow-2xs flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#A91121]/10 text-[#A91121] shrink-0">
            <Target className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-foreground tracking-tight leading-none">
              {(bestClassificationAccuracy * 100).toFixed(1)}%
            </div>
            <div className="text-[11px] font-semibold text-foreground mt-0.5">Best Classification Accuracy</div>
            <div className="text-[10px] text-muted-foreground font-mono">(v2.0)</div>
          </div>
        </div>

        {/* Card 3: Fastest Speed */}
        <div className="p-2.5 sm:p-3 rounded-xl border border-border bg-card shadow-2xs flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#A91121]/10 text-[#A91121] shrink-0">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-foreground tracking-tight leading-none">
              {fastestSpeed} FPS
            </div>
            <div className="text-[11px] font-semibold text-foreground mt-0.5">Fastest Speed</div>
            <div className="text-[10px] text-muted-foreground font-mono">(v2.0)</div>
          </div>
        </div>

        {/* Card 4: Recommended Parameters */}
        <div className="p-2.5 sm:p-3 rounded-xl border border-border bg-card shadow-2xs flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#A91121]/10 text-[#A91121] shrink-0">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xl sm:text-2xl font-black text-foreground tracking-tight leading-none">
              {recommendedModel.parameters}
            </div>
            <div className="text-[11px] font-semibold text-foreground mt-0.5">Recommended Parameters</div>
            <div className="text-[10px] text-muted-foreground font-mono">({recommendedModel.version})</div>
          </div>
        </div>
      </div>

      {/* View Switcher Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-1 rounded-xl bg-white dark:bg-card border border-border shadow-2xs">
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            type="button"
            onClick={() => setActiveTab('scorecard')}
            className={`px-3.5 py-1.5 text-xs rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'scorecard'
                ? 'bg-[#A91121] text-white font-bold shadow-sm'
                : 'text-slate-600 hover:text-[#A91121] hover:bg-red-50/60 font-semibold'
            }`}
          >
            <BarChart2 className="w-3.5 h-3.5" />
            Metric Scorecard
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('radar')}
            className={`px-3.5 py-1.5 text-xs rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'radar'
                ? 'bg-[#A91121] text-white font-bold shadow-sm'
                : 'text-slate-600 hover:text-[#A91121] hover:bg-red-50/60 font-semibold'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Radar Tradeoffs
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('qualitative')}
            className={`px-3.5 py-1.5 text-xs rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'qualitative'
                ? 'bg-[#A91121] text-white font-bold shadow-sm'
                : 'text-slate-600 hover:text-[#A91121] hover:bg-red-50/60 font-semibold'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Visual Comparison
          </button>
        </div>
        <div className="hidden md:flex items-center gap-2 pr-3 text-[11px] font-mono text-muted-foreground">
          <span>Architectural Benchmark Telemetry</span>
        </div>
      </div>

      {/* Tab 1: Modernized Metric Scorecard */}
      {activeTab === 'scorecard' && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 sm:gap-4 items-start">
            
            {/* Left Column: 2x2 Model Versions Grid */}
            <div className="lg:col-span-7 space-y-2.5">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-[#A91121]" />
                <h3 className="text-xs sm:text-sm font-bold text-foreground">Model Versions Overview</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 sm:gap-3">
                {models.map((m) => {
                  const isSelected = m.id === selectedModelId;
                  const isRecommended = m.id === 'MOD-201';

                  return (
                    <div
                      key={m.id}
                      onClick={() => setSelectedModelId(m.id)}
                      className={`relative rounded-xl bg-card p-3 transition-all cursor-pointer border ${
                        isRecommended
                          ? 'border-2 border-[#A91121] shadow-xs'
                          : isSelected
                          ? 'border-[#A91121]/60 ring-2 ring-[#A91121]/20 shadow-xs'
                          : 'border-border hover:border-slate-300 dark:hover:border-slate-700 shadow-2xs'
                      }`}
                    >
                      {/* Recommended Ribbon */}
                      {isRecommended && (
                        <div className="absolute top-0 right-0 bg-[#A91121] text-white text-[9px] font-extrabold px-2 py-0.5 rounded-bl-lg rounded-tr-lg tracking-wider flex items-center gap-1 shadow-2xs">
                          <CheckCircle2 className="w-2.5 h-2.5" />
                          RECOMMENDED
                        </div>
                      )}

                      {/* Header */}
                      <div className="flex items-start gap-2">
                        <span className="px-1.5 py-0.5 rounded border border-border font-mono font-bold text-[11px] text-foreground bg-muted/40 shrink-0">
                          {m.version}
                        </span>
                        <div className="min-w-0 pr-8">
                          <h4 className="font-bold text-xs sm:text-sm text-foreground leading-snug">{m.name}</h4>
                          <p className="text-[10px] text-muted-foreground truncate">{m.category}</p>
                        </div>
                      </div>

                      {/* Status Badge */}
                      <div className="mt-2">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            m.isActive
                              ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30'
                              : 'bg-muted text-muted-foreground border-border'
                          }`}
                        >
                          {m.isActive ? (
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          ) : (
                            <Clock className="w-3 h-3 text-muted-foreground" />
                          )}
                          {m.status}
                        </span>
                      </div>

                      {/* 3-Metric Strip */}
                      <div className="grid grid-cols-3 gap-1.5 py-1.5 border-y border-border/60 my-2 text-center">
                        {m.id === 'MOD-200' ? (
                          <>
                            <div>
                              <div className="text-[10px] uppercase font-semibold text-muted-foreground">Sensitivity</div>
                              <div className="font-bold font-mono text-xs text-foreground mt-0.5">
                                {(m.recall * 100).toFixed(1)}%
                              </div>
                            </div>
                            <div>
                              <div className="text-[10px] uppercase font-semibold text-muted-foreground">Specificity</div>
                              <div className="font-bold font-mono text-xs text-foreground mt-0.5">
                                {(m.specificity * 100).toFixed(1)}%
                              </div>
                            </div>
                            <div>
                              <div className="text-[10px] uppercase font-semibold text-muted-foreground">Accuracy</div>
                              <div className="font-bold font-mono text-xs text-foreground mt-0.5">
                                {(m.accuracy * 100).toFixed(1)}%
                              </div>
                            </div>
                          </>
                        ) : (
                          <>
                            <div>
                              <div className="text-[10px] uppercase font-semibold text-muted-foreground">Dice</div>
                              <div className="font-bold font-mono text-xs text-foreground mt-0.5">
                                {m.dice && m.dice > 0 ? `${(m.dice * 100).toFixed(2)}%` : 'N/A'}
                              </div>
                            </div>
                            <div>
                              <div className="text-[10px] uppercase font-semibold text-muted-foreground">IoU</div>
                              <div className="font-bold font-mono text-xs text-foreground mt-0.5">
                                {m.iou && m.iou > 0 ? `${(m.iou * 100).toFixed(2)}%` : 'N/A'}
                              </div>
                            </div>
                            <div>
                              <div className="text-[10px] uppercase font-semibold text-muted-foreground">Accuracy</div>
                              <div className="font-bold font-mono text-xs text-foreground mt-0.5">
                                {(m.accuracy * 100).toFixed(1)}%
                              </div>
                            </div>
                          </>
                        )}
                      </div>

                      {/* Footer Specs */}
                      <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Zap className="w-3 h-3 text-muted-foreground" />
                          <span>{m.throughputFps} FPS</span>
                        </div>
                        {m.id === 'MOD-200' ? (
                          <div className="text-[10px] font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                            MAE: 9.54% • Diagnostic Head
                          </div>
                        ) : (
                          <div className="flex items-center gap-1">
                            <Cpu className="w-3 h-3 text-muted-foreground" />
                            <span>{m.parameters} params</span>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right Column: Benchmark Comparison Chart & Performance Insights */}
            <div className="lg:col-span-5 space-y-2.5">
              
              {/* Benchmark Comparison Card */}
              <div className="p-3.5 rounded-xl border border-border bg-card shadow-xs space-y-2.5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-[#A91121]" />
                    <h3 className="text-xs sm:text-sm font-bold text-foreground">Benchmark Comparison</h3>
                  </div>

                  {/* Metric Toggle Pills */}
                  <div className="flex flex-wrap items-center gap-1">
                    {(['accuracy', 'dice', 'iou', 'speed', 'params'] as const).map((metricKey) => {
                      const labels: Record<string, string> = {
                        accuracy: 'Accuracy',
                        dice: 'Dice',
                        iou: 'IoU',
                        speed: 'Speed (FPS)',
                        params: 'Parameters'
                      };
                      const isActive = benchmarkMetric === metricKey;
                      return (
                        <button
                          key={metricKey}
                          type="button"
                          onClick={() => setBenchmarkMetric(metricKey)}
                          className={`px-1.5 py-0.5 text-[10px] rounded transition-all font-semibold cursor-pointer ${
                            isActive
                              ? 'bg-[#A91121] text-white shadow-2xs'
                              : 'bg-muted/60 text-muted-foreground hover:bg-muted border border-border/60'
                          }`}
                        >
                          {labels[metricKey]}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Vertical Bar Chart */}
                {(() => {
                  const chartData = getBarData(benchmarkMetric);
                  return (
                    <div className="space-y-2 pt-1">
                      <div className="relative h-36 flex items-end justify-between gap-3 px-2 pt-6 pb-2 border-b border-border/80">
                        
                        {/* Y-Axis Label and Grid Guidelines */}
                        <div className="absolute left-0 top-0 bottom-6 flex flex-col justify-between text-[9px] font-mono text-muted-foreground pointer-events-none select-none">
                          {chartData.yTicks.map((tick, i) => (
                            <span key={i} className="leading-none">{tick}</span>
                          ))}
                        </div>

                        {/* Chart Grid Lines */}
                        <div className="absolute left-8 right-0 top-0 bottom-6 flex flex-col justify-between pointer-events-none">
                          {chartData.yTicks.map((_, i) => (
                            <div key={i} className="border-b border-dashed border-border/40 w-full" />
                          ))}
                        </div>

                        {/* Bars Container */}
                        <div className="w-full pl-8 h-full flex items-end justify-around gap-2.5 relative z-10">
                          {chartData.bars.map((bar) => {
                            const isSegmentation = bar.isPrimary;
                            const barColorClass = isSegmentation
                              ? 'bg-[#A91121] hover:bg-[#8B0E1B]'
                              : 'bg-red-400 hover:bg-red-500';

                            return (
                              <div
                                key={bar.id}
                                className="flex-1 flex flex-col items-center justify-end h-full max-w-[56px] group"
                              >
                                {/* Value Callout */}
                                <span className="text-[9px] font-bold font-mono text-foreground mb-1 group-hover:scale-105 transition-transform truncate">
                                  {bar.displayValue}
                                </span>

                                {/* Vertical Bar */}
                                <div
                                  style={{ height: `${bar.heightPct}%` }}
                                  className={`w-full rounded-t-sm transition-all duration-300 shadow-2xs ${barColorClass}`}
                                />
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* X-Axis Labels */}
                      <div className="pl-8 grid grid-cols-4 gap-1.5 text-center">
                        {chartData.bars.map((bar) => (
                          <div key={bar.id} className="min-w-0">
                            <span className="block font-mono font-bold text-[11px] text-foreground">{bar.version}</span>
                            <span className="block text-[9px] text-muted-foreground truncate">{bar.name}</span>
                          </div>
                        ))}
                      </div>

                      {/* Footnote */}
                      <p className="text-[9px] text-muted-foreground italic">
                        {chartData.footnote}
                      </p>
                    </div>
                  );
                })()}
              </div>

              {/* Consolidated Performance Insights & Architecture Summary Card */}
              <div className="p-3.5 rounded-xl border border-border bg-card shadow-xs space-y-2.5">
                <div className="flex items-center justify-between border-b border-border/80 pb-2">
                  <div className="flex items-center gap-1.5">
                    <TrendingUp className="w-4 h-4 text-[#A91121]" />
                    <h3 className="text-xs sm:text-sm font-bold text-foreground">Performance Insights & Architecture Summary</h3>
                  </div>
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-muted text-foreground border border-border">
                    v2.1 Recommended
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex items-start gap-2 p-2 rounded-lg bg-muted/40 dark:bg-muted/10 border border-border/60">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <p className="text-[11px] text-muted-foreground leading-snug">
                      <strong className="text-foreground">Attention Gating Leader (v1.1):</strong> Achieves top vessel accuracy (98.6%) and Dice (68.33%) by filtering non-vascular thoracic artifacts.
                    </p>
                  </div>

                  <div className="flex items-start gap-2 p-2 rounded-lg bg-muted/40 dark:bg-muted/10 border border-border/60">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <p className="text-[11px] text-muted-foreground leading-snug">
                      <strong className="text-foreground">Diagnostic Classifier (v2.0):</strong> Fastest raw inference (70.42 FPS) with 87.4% accuracy, sub-10% (9.54%) %DS MAE, and native Grad-CAM attribution.
                    </p>
                  </div>

                  <div className="flex items-start gap-2 p-2 rounded-lg bg-muted/40 dark:bg-muted/10 border border-[#A91121]/30 ring-1 ring-[#A91121]/10">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#A91121] shrink-0 mt-0.5" />
                    <p className="text-[11px] text-foreground leading-snug">
                      <strong className="text-[#A91121]">StenoVision Hybrid Cascade (v2.1):</strong> Integrated end-to-end clinical workflow uniting Attention U-Net &amp; ResNet-18 with Soft-NMS filtering (42% false-positive reduction) at real-time 29.8 FPS (&gt;25 FPS fluoroscopy standard).
                    </p>
                  </div>
                </div>

                {/* 3 Inline Proof Badges */}
                <div className="flex flex-wrap items-center gap-1.5 pt-0.5 text-[10px] font-mono">
                  <span className="px-2 py-0.5 rounded bg-muted text-foreground border border-border/80 font-semibold">
                    ✓ End-to-End Workflow
                  </span>
                  <span className="px-2 py-0.5 rounded bg-muted text-foreground border border-border/80 font-semibold">
                    ✓ 42% False Positive Suppression
                  </span>
                  <span className="px-2 py-0.5 rounded bg-muted text-foreground border border-border/80 font-semibold">
                    ✓ 29.8 FPS Intraoperative
                  </span>
                </div>
              </div>

            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Radar Trade-Off Analysis */}
      {activeTab === 'radar' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 p-6 rounded-xl border border-border bg-card shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-[#A91121]" />
                <h4 className="text-sm font-bold text-foreground">
                  Multi-Dimensional Model Trade-Off Radar
                </h4>
              </div>
              <span className="text-xs text-muted-foreground font-mono">
                Normalized Score (0-100)
              </span>
            </div>
            <div className="h-80 flex items-center justify-center">
              <Radar data={radarData} options={radarOptions} />
            </div>
          </div>

          <div className="p-6 rounded-xl border border-border bg-card shadow-xs space-y-4">
            <h4 className="text-sm font-bold text-foreground flex items-center gap-2 border-b border-border pb-3">
              <TrendingUp className="w-4 h-4 text-[#A91121]" />
              Key Benchmarking Findings
            </h4>
            <div className="space-y-3 text-xs leading-relaxed text-muted-foreground">
              <div className="p-3 rounded-lg bg-muted/40 border border-border">
                <strong className="text-foreground block mb-1">Attention Gating Advantage:</strong>
                Attention U-Net v1.1 improves IoU from 53.25% to 53.56% and precision to 73.40% over Baseline v1.0 by selectively filtering background bone/catheter artifacts.
              </div>
              <div className="p-3 rounded-lg bg-muted/40 border border-border">
                <strong className="text-foreground block mb-1">Dual-Head ResNet-18 Precision:</strong>
                ResNet-18 Severity Network v2.0 delivers 87.43% binary classification accuracy and 9.54% %DS MAE at 70.4 FPS inference speed.
              </div>
              <div className="p-3 rounded-lg bg-muted/40 border border-border">
                <strong className="text-foreground block mb-1">Recommended Architecture Synergies:</strong>
                StenoVision Cascade v2.1 maintains real-time 29.8 FPS fluoroscopy compliance while producing complete quantitative QCA metrics and Grad-CAM visual proofs.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Side-by-Side Qualitative Inference Comparison */}
      {activeTab === 'qualitative' && (() => {
        const is3D = benchmarkCase.startsWith('PA');
        return (
          <div className="space-y-4 p-6 rounded-xl border border-border bg-card shadow-xs">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-border pb-4">
              <div>
                <h4 className="text-sm font-bold text-foreground flex items-center gap-2">
                  <Layers className="w-4 h-4 text-[#A91121]" />
                  Multi-Model Inference & Qualitative Proof Gallery
                </h4>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Step-by-step diagnostic breakdown across architectures: Raw fluoroscopy / CCTA &rarr; Baseline segmentation &rarr; Attention gating &rarr; Grad-CAM XAI localization.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground font-medium">Benchmark Case:</span>
                <select
                  value={benchmarkCase}
                  onChange={(e) => setBenchmarkCase(e.target.value as any)}
                  className="text-xs py-1.5 px-3 rounded-md bg-background border border-border focus:outline-none font-medium cursor-pointer"
                >
                  <optgroup label="2D Coronary Angiograms (XCA)">
                    <option value="10">CASE-1010 (Mid-LAD 64.7% DS – Moderate)</option>
                    <option value="35">CASE-1035 (Prox-RCA 78.4% DS – Severe)</option>
                    <option value="110">CASE-1090 (Subtotal LAD 94.2% DS – Critical)</option>
                  </optgroup>
                  <optgroup label="3D Volumetric Computed Tomography (CCTA)">
                    <option value="PA000042">CASE-CCTA-042 (3D Volumetric LAD 70.3% DS – Severe)</option>
                    <option value="PA000024">CASE-CCTA-024 (3D Volumetric LCx 68.5% DS – Significant)</option>
                  </optgroup>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2">
              
              {/* Panel 1: Original Raw Scan */}
              <div className="rounded-lg border border-border overflow-hidden bg-muted/20">
                <div className="px-3 py-1.5 bg-muted/60 border-b border-border flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground">
                    {is3D ? '1. Raw 3D CCTA Axial' : '1. Raw Input XCA'}
                  </span>
                  <span className="text-[10px] text-muted-foreground font-mono">
                    {is3D ? '3D Volume' : '512×512'}
                  </span>
                </div>
                <div className="relative aspect-square bg-black flex items-center justify-center">
                  <Image
                    src={`/assets/cases/${benchmarkCase}.png`}
                    alt={is3D ? '3D Volumetric CCTA' : 'Raw Angiogram'}
                    fill
                    className="object-contain"
                    unoptimized
                  />
                </div>
                <div className="p-2.5 text-[11px] text-muted-foreground border-t border-border">
                  {is3D
                    ? 'High-resolution 3D volumetric axial CT slice capturing coronary cross-section & calcified plaque.'
                    : 'Standard cine-angiogram with background thoracic and rib attenuation.'}
                </div>
              </div>

              {/* Panel 2: Baseline U-Net Prediction */}
              <div className="rounded-lg border border-border overflow-hidden bg-muted/20">
                <div className="px-3 py-1.5 bg-muted/60 border-b border-border flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground">2. Baseline U-Net (v1.0)</span>
                  <span className="text-[10px] text-blue-600 font-mono">Dice: 68.22%</span>
                </div>
                <div className="relative aspect-square bg-black flex items-center justify-center">
                  <Image
                    src={`/assets/cases/${benchmarkCase}_mask.png`}
                    alt="Baseline Mask"
                    fill
                    className="object-contain"
                    unoptimized
                  />
                </div>
                <div className="p-2.5 text-[11px] text-muted-foreground border-t border-border">
                  {is3D
                    ? 'Volumetric slice vessel tracking contour with standard convolutional skip connections.'
                    : 'Captures main coronary trunk with minor edge noise on micro-branches.'}
                </div>
              </div>

              {/* Panel 3: Attention U-Net Prediction */}
              <div className="rounded-lg border border-border overflow-hidden bg-muted/20">
                <div className="px-3 py-1.5 bg-muted/60 border-b border-border flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground">3. Attention U-Net (v1.1)</span>
                  <span className="text-[10px] text-emerald-600 font-mono">Dice: 68.33%</span>
                </div>
                <div className="relative aspect-square bg-black flex items-center justify-center">
                  <Image
                    src={`/assets/cases/${benchmarkCase}_mask.png`}
                    alt="Attention Mask"
                    fill
                    className="object-contain"
                    unoptimized
                  />
                </div>
                <div className="p-2.5 text-[11px] text-muted-foreground border-t border-border">
                  {is3D
                    ? 'Additive soft-attention gating isolates vessel wall and suppresses myocardial tissue noise.'
                    : 'Sharp lumen contours, suppressed background artifacts, superior distal sensitivity.'}
                </div>
              </div>

              {/* Panel 4: ResNet-18 Grad-CAM Attribution */}
              <div className="rounded-lg border border-border overflow-hidden bg-muted/20">
                <div className="px-3 py-1.5 bg-muted/60 border-b border-border flex items-center justify-between">
                  <span className="text-xs font-semibold text-foreground">4. StenoVision Grad-CAM (v2.1)</span>
                  <span className="text-[10px] text-red-600 font-mono">Acc: 87.43%</span>
                </div>
                <div className="relative aspect-square bg-black flex items-center justify-center">
                  <Image
                    src={`/assets/cases/${benchmarkCase}_heatmap.png`}
                    alt="Grad-CAM Saliency"
                    fill
                    className="object-contain"
                    unoptimized
                  />
                </div>
                <div className="p-2.5 text-[11px] text-muted-foreground border-t border-border">
                  {is3D
                    ? 'Volumetric attention localization pinpointing peak arterial narrowing on multi-slice reconstruction.'
                    : 'Localized spatial activation focusing directly over the stenotic bottleneck.'}
                </div>
              </div>

            </div>
          </div>
        );
      })()}

    </div>
  );
};
