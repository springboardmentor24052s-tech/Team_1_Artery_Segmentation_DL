'use client';

import React, { useState } from 'react';
import { SummaryCard } from '../SummaryCard';
import { UserAvatar } from '../UserAvatar';
import { MedicalCase, DASHBOARD_STATS, INITIAL_CASES, INITIAL_USERS, AI_ANALYSIS_SUMMARY, SystemUser } from '@/lib/mockData';
import {
  FolderKanban,
  Activity,
  CheckCircle,
  Clock,
  ArrowUpRight,
  Cpu,
  ShieldCheck,
  Stethoscope,
  UploadCloud,
  FileText,
  Sliders,
  Layers,
  Server,
  Zap,
  AlertTriangle,
  Play,
  Terminal,
  Database,
  RefreshCw,
  CheckCircle2,
  UserCheck,
  Shield,
  Eye,
  Monitor,
  Home,
  BarChart2,
  Settings,
  Microscope,
  ClipboardList,
  ArrowLeft,
  Folder,
  Users
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface DashboardScreenProps {
  currentUser: SystemUser;
  onNavigate: (screen: string, caseId?: string) => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ currentUser, onNavigate }) => {
  const recentCases = INITIAL_CASES.slice(0, 5);
  const [devPerspective, setDevPerspective] = useState<'master' | 'clinician' | 'researcher' | 'datascientist' | 'admin'>('master');

  // =========================================================================
  // Standardized Shared Diagnostic Datasets (Section 13 Specification)
  // =========================================================================

  // 1. 5-Tier Stenosis Severity Distribution (Section 13, Page 14)
  const severityBarData = {
    labels: AI_ANALYSIS_SUMMARY.severityDistribution.labels,
    datasets: [
      {
        label: 'Analyzed Angiograms',
        data: AI_ANALYSIS_SUMMARY.severityDistribution.data,
        backgroundColor: AI_ANALYSIS_SUMMARY.severityDistribution.colors,
        borderRadius: 6,
      },
    ],
  };

  const severityDoughnutData = {
    labels: AI_ANALYSIS_SUMMARY.severityDistribution.labels,
    datasets: [
      {
        data: AI_ANALYSIS_SUMMARY.severityDistribution.data,
        backgroundColor: AI_ANALYSIS_SUMMARY.severityDistribution.colors,
        borderWidth: 2,
      },
    ],
  };

  // 2. Coronary Artery Lesion Territory Distribution (AHA Mapping)
  const radBarData = {
    labels: ['LAD (Left Anterior)', 'RCA (Right Coronary)', 'LCx (Circumflex)', 'LMCA (Left Main)'],
    datasets: [
      {
        label: 'Flagged Lesions',
        data: [12, 8, 5, 2],
        backgroundColor: '#A91121',
        borderRadius: 6,
      },
    ],
  };

  // 3. Neural Network Loss Convergence (Epoch 1 to 30)
  const trainingLossData = {
    labels: ['Epoch 5', 'Epoch 10', 'Epoch 15', 'Epoch 20', 'Epoch 25', 'Epoch 30'],
    datasets: [
      {
        label: 'Attention U-Net Dice Loss',
        data: [0.52, 0.41, 0.35, 0.33, 0.32, 0.3167],
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.3,
        fill: true,
      },
      {
        label: 'Faster R-CNN Val Loss',
        data: [0.38, 0.28, 0.22, 0.19, 0.178, 0.1713],
        borderColor: '#10B981',
        tension: 0.3,
      },
    ],
  };

  // 4. Clinical Research Cohort Progress
  const studyBarData = {
    labels: ['ARCADE Cohort A', 'ARCADE Cohort B', 'Validation Trial 1', 'Prospective Cohort'],
    datasets: [
      {
        label: 'Enrolled Angiograms',
        data: [650, 550, 200, 100],
        backgroundColor: '#8B5CF6',
        borderRadius: 6,
      },
    ],
  };

  // 5. Inter-Observer Consensus Concordance
  const studyDoughnutData = {
    labels: ['Consensus Achieved (Dice >0.65)', 'Pending Research Review', 'Resolved Discordance'],
    datasets: [
      {
        data: [1380, 85, 35],
        backgroundColor: ['#10B981', '#F59E0B', '#8B5CF6'],
        borderWidth: 2,
      },
    ],
  };

  // =========================================================================
  // Reusable Section 13 UI Components
  // =========================================================================

  // Role Perspective Simulated View Banner (Matches User Design Mockup)
  const renderRolePerspectiveBanner = (roleTitle: string) => (
    <div className="bg-red-50/50 border border-red-200/80 rounded-xl px-4 py-2.5 flex items-center justify-between shadow-2xs">
      <div className="flex items-center gap-3 text-xs sm:text-sm text-slate-800">
        <ClipboardList className="w-4 h-4 text-[#A91121] shrink-0" />
        <div className="h-4 w-px bg-red-200" />
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="font-bold text-[#252525]">Role View:</span>
          <span className="text-slate-700">{roleTitle}</span>
        </div>
      </div>
      <button
        onClick={() => setDevPerspective('master')}
        className="px-3.5 py-1.5 bg-[#A91121] hover:bg-[#800D1B] text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 shadow-2xs cursor-pointer"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Return to Developer View</span>
      </button>
    </div>
  );

  // Core Section 13 Case Accounting Grid (Page 14) & Section 15 Alert Banner
  const renderSection13AccountingGrid = (badgeSubtitle?: string) => (
    <div className="space-y-4">
      {/* Section 15 Clinical Alert & Notification System Banner */}
      <div className="relative overflow-hidden rounded-xl border border-red-500/40 bg-gradient-to-r from-red-500/15 via-red-500/5 to-transparent p-4 shadow-sm">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-red-500/20 text-[#A91121] shrink-0 mt-0.5">
              <AlertTriangle className="w-5 h-5 animate-bounce" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2 py-0.5 text-[11px] font-bold rounded bg-red-600 text-white uppercase tracking-wider">
                  Critical Lesion Alert
                </span>
                <span className="text-xs font-mono font-semibold text-[#A91121]">
                  CASE-1090 · David K. Vance (67M)
                </span>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-red-100 text-red-800 font-bold border border-red-200">
                  94.2% Subtotal Occlusion
                </span>
                <span className="text-[11px] font-semibold text-red-700">
                  TIMI 0/1 Flow Risk
                </span>
              </div>
              <p className="text-xs text-slate-700 mt-1 leading-snug">
                <strong>Proximal LAD (Segment 6)</strong> severe bottleneck lesion with MLD 0.20 mm (RVD 3.45 mm). Indication: Immediate Catheterization Laboratory activation for urgent revascularization.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 w-full md:w-auto justify-end">
            <button
              onClick={() => onNavigate('case-detail', 'CASE-1090')}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-white border border-red-300 text-red-800 hover:bg-red-50 transition-colors shadow-2xs"
            >
              Audit Case & Calipers
            </button>
            <button
              onClick={() => onNavigate('reports')}
              className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-[#A91121] text-white hover:bg-[#8B0E1B] transition-colors shadow-sm flex items-center gap-1.5"
            >
              <FileText className="w-3.5 h-3.5" /> Clinical Report
            </button>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
          <Activity className="w-4 h-4 text-[#A91121]" /> Analysis Overview
        </h3>
        <span className="text-[11px] font-mono text-slate-500">
          {badgeSubtitle || 'Evaluation Summary · 1,514 Total Cases'}
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="Total Cases"
          value={AI_ANALYSIS_SUMMARY.totalCasesAnalyzed.toLocaleString()}
          change="1,500 ARCADE + 14 Live"
          isPositive={true}
          icon={BarChart2}
          description="Attention U-Net & ResNet-18 Severity Network"
        />
        <SummaryCard
          title="Normal Findings"
          value={AI_ANALYSIS_SUMMARY.normalCases.toLocaleString()}
          change="20.6% Normal"
          isPositive={true}
          icon={CheckCircle2}
          description="Normal baseline (<25% caliber reduction)"
        />
        <SummaryCard
          title="Abnormal Findings"
          value={AI_ANALYSIS_SUMMARY.abnormalCases.toLocaleString()}
          change="79.4% Abnormal"
          isPositive={false}
          icon={AlertTriangle}
          description="Abnormal findings detected"
        />
        <SummaryCard
          title="Stenosis Cases"
          value={AI_ANALYSIS_SUMMARY.detectedStenosisCases.toLocaleString()}
          change="Stenosis Detected"
          isPositive={false}
          icon={Activity}
          description="Detected stenosis regions"
        />
      </div>
    </div>
  );

  // Section 13 Recent Analyses & Processing Status Queue Table (Page 14)
  const renderRecentAnalysesTable = (titleText: string, subtitleText: string) => (
    <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-[#A91121]/15 pb-4">
        <div>
          <h3 className="text-sm font-bold text-[#252525] flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#A91121]" /> {titleText}
          </h3>
          <p className="text-xs text-slate-500">{subtitleText}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            1,480 Completed · 14 Active Queue
          </span>
          <button
            onClick={() => onNavigate('cases')}
            className="px-3 py-1.5 bg-[#F5F5F5] hover:bg-[#E2E2E2] text-xs font-semibold text-slate-700 rounded-lg transition-colors flex items-center gap-1.5"
          >
            All Cases <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left">
          <thead className="bg-[#FAFBFD] border-b border-[#A91121]/15 text-slate-600 font-mono uppercase text-[11px]">
            <tr>
              <th className="py-2.5 px-3">Case ID</th>
              <th className="py-2.5 px-3">Patient</th>
              <th className="py-2.5 px-3">Vessel & Location</th>
              <th className="py-2.5 px-3">Measured %DS</th>
              <th className="py-2.5 px-3">MLD / RVD</th>
              <th className="py-2.5 px-3">Severity Tier</th>
              <th className="py-2.5 px-3">AI Confidence</th>
              <th className="py-2.5 px-3">Processing Status</th>
              <th className="py-2.5 px-3 text-right">Diagnostic Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#A91121]/15">
            {recentCases.map((c, idx) => {
              const confidenceScores = ['96.8%', '94.2%', '95.1%', '91.4%', '98.0%'];
              const conf = confidenceScores[idx % confidenceScores.length];
              const segCode = c.primaryVessel === 'LAD' ? 'Segment 7 (Mid)' :
                              c.primaryVessel === 'RCA' ? 'Segment 1 (Proximal)' :
                              c.primaryVessel === 'LM' ? 'Segment 5 (Bifurcation)' : 'Segment 11 (Circumflex)';

              return (
                <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-2.5 px-3 font-mono font-bold text-slate-800">{c.id}</td>
                  <td className="py-2.5 px-3 font-semibold text-[#252525]">{c.patientName}</td>
                  <td className="py-2.5 px-3 font-mono text-slate-600">
                    <span className="font-bold text-slate-800">{c.primaryVessel}</span> ({segCode})
                  </td>
                  <td className="py-2.5 px-3 font-mono font-bold text-[#A91121]">{c.maxStenosisPercent}%</td>
                  <td className="py-2.5 px-3 font-mono text-slate-600">{c.mldMm || '0.50'} mm / {c.rvdMm || '2.88'} mm</td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      c.severityCategory === 'Severe' ? 'bg-red-100 text-red-800 border border-red-200' :
                      c.severityCategory === 'Moderate' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                      'bg-blue-100 text-blue-800 border border-blue-200'
                    }`}>
                      {c.severityCategory}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-emerald-700 font-semibold">{conf}</td>
                  <td className="py-2.5 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
                      {c.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => onNavigate('case-detail', c.id)}
                        className="px-2.5 py-1 bg-red-50 text-[#A91121] hover:bg-red-100 rounded text-[11px] font-semibold transition-colors border border-red-200"
                      >
                        Inspect XAI
                      </button>
                      <button
                        onClick={() => onNavigate('reports')}
                        className="px-2.5 py-1 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded text-[11px] font-semibold transition-colors border border-slate-200"
                        title="View or generate automated report"
                      >
                        Report
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );

  // =========================================================================
  // 0. DEVELOPER / SUPERUSER MASTER DASHBOARD (Sathiya)
  // =========================================================================
  if (currentUser.role === 'Developer') {
    return (
      <div className="space-y-6">
        {/* Developer Analysis & Control Card */}
        <div className="bg-white border border-[#A91121]/20 rounded-2xl p-5 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <Monitor className="w-6 h-6 text-[#A91121] shrink-0" />
              <div className="flex items-center gap-2.5">
                <h2 className="text-lg font-bold text-[#111827] tracking-tight">Developer Dashboard</h2>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-red-50 text-[#A91121] border border-red-200 uppercase tracking-wider">
                  SUPERUSER
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                CUDA 12.8 · NVIDIA RTX 2050 (29.8 FPS · 31.4ms)
              </span>
            </div>
          </div>

          {/* Integrated Role View Toolbar */}
          <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-700 font-mono tracking-wider">
              <Settings className="w-4 h-4 text-slate-600" />
              <span>ROLE VIEW:</span>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {[
                { id: 'master', label: 'All-Inclusive View', icon: Home },
                { id: 'clinician', label: 'Clinician View', icon: Stethoscope },
                { id: 'datascientist', label: 'Data Scientist View', icon: BarChart2 },
                { id: 'researcher', label: 'Researcher View', icon: Microscope },
                { id: 'admin', label: 'Administrator View', icon: Shield },
              ].map((pill) => {
                const Icon = pill.icon;
                const isSelected = devPerspective === pill.id;
                return (
                  <button
                    key={pill.id}
                    onClick={() => setDevPerspective(pill.id as any)}
                    className={`px-3.5 py-1.5 text-xs rounded-lg transition-all flex items-center gap-1.5 font-medium cursor-pointer ${
                      isSelected
                        ? 'bg-[#A91121] text-white shadow-xs font-semibold'
                        : 'bg-white text-slate-700 hover:text-[#A91121] border border-[#A91121]/20 hover:border-[#A91121]/40'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-white' : 'text-slate-600'}`} />
                    <span>{pill.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Quick Sandbox Action Bar */}
        <div className="bg-white border border-[#A91121]/20 rounded-xl p-3.5 shadow-2xs flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs font-semibold text-slate-700">Quick Actions:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => onNavigate('upload')}
              className="px-3 py-1.5 text-xs font-semibold bg-[#A91121] hover:bg-[#800D1B] text-white rounded-lg transition-colors flex items-center gap-1.5 shadow-2xs cursor-pointer"
            >
              <UploadCloud className="w-3.5 h-3.5" /> Upload Scan
            </button>
            <button
              onClick={() => onNavigate('config')}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-[#A91121]/20 hover:border-[#A91121] text-slate-700 hover:text-[#A91121] rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <Cpu className="w-3.5 h-3.5 text-slate-500" /> Model Settings
            </button>
            <button
              onClick={() => onNavigate('results')}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-[#A91121]/20 hover:border-[#A91121] text-slate-700 hover:text-[#A91121] rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <Activity className="w-3.5 h-3.5 text-slate-500" /> Review Analysis
            </button>
            <button
              onClick={() => onNavigate('cases')}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-[#A91121]/20 hover:border-[#A91121] text-slate-700 hover:text-[#A91121] rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <Folder className="w-3.5 h-3.5 text-slate-500" /> View Cases
            </button>
            <button
              onClick={() => onNavigate('reports')}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-[#A91121]/20 hover:border-[#A91121] text-slate-700 hover:text-[#A91121] rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5 text-slate-500" /> Clinical Reports
            </button>
            <button
              onClick={() => onNavigate('users')}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-[#A91121]/20 hover:border-[#A91121] text-slate-700 hover:text-[#A91121] rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <Users className="w-3.5 h-3.5 text-slate-500" /> Manage Users
            </button>
          </div>
        </div>

        {/* Dynamic Perspective Content */}
        {devPerspective === 'clinician' ? (
          <div className="space-y-6">
            {renderRolePerspectiveBanner('Radiologist / Clinician Workflow & Analysis')}
            {renderSection13AccountingGrid('Clinician Cohort View · Active Reading Queue')}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
                <h3 className="text-sm font-bold text-[#252525] mb-4">Stenosis Severity Distribution</h3>
                <div className="h-64">
                  <Bar data={severityBarData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>
              <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
                <h3 className="text-sm font-bold text-[#252525] mb-4">Artery Lesion Territory Distribution (AHA Mapping)</h3>
                <div className="h-64">
                  <Bar data={radBarData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>
            </div>
            {renderRecentAnalysesTable('Recent Diagnostic Analyses Queue', 'Live patient scans queued for quantitative QCA morphometry and clinical sign-off')}
          </div>
        ) : devPerspective === 'datascientist' ? (
          <div className="space-y-6">
            {renderRolePerspectiveBanner('Data Scientist Workflow & Analysis')}
            {renderSection13AccountingGrid('Model Evaluation View · 300 Test Scans Benchmark')}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
                <h3 className="text-sm font-bold text-[#252525] mb-4">Model Training Performance: Attention U-Net & Faster R-CNN</h3>
                <div className="h-64">
                  <Line data={trainingLossData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>
              <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
                <h3 className="text-sm font-bold text-[#252525] mb-4">5-Tier Severity Detection Distribution</h3>
                <div className="h-64 flex items-center justify-center">
                  <Doughnut data={severityDoughnutData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>
            </div>
            {renderRecentAnalysesTable('Validation Benchmark Scan Queue', 'Automated inference testing across ARCADE validation split')}
          </div>
        ) : devPerspective === 'researcher' ? (
          <div className="space-y-6">
            {renderRolePerspectiveBanner('Medical Researcher Workflow & Analysis')}
            {renderSection13AccountingGrid('Clinical Research View · ARCADE Multi-Center Trial')}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
                <h3 className="text-sm font-bold text-[#252525] mb-4">Study Cohort Enrollment Distribution</h3>
                <div className="h-64">
                  <Bar data={studyBarData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>
              <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
                <h3 className="text-sm font-bold text-[#252525] mb-4">Inter-Observer Consensus Concordance Breakdown</h3>
                <div className="h-64 flex items-center justify-center">
                  <Doughnut data={studyDoughnutData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>
            </div>
            {renderRecentAnalysesTable('Cohort Study Repository & Annotation Queue', 'Multi-center clinical trial cohort consensus audit')}
          </div>
        ) : devPerspective === 'admin' ? (
          <div className="space-y-6">
            {renderRolePerspectiveBanner('Administrator Workflow & Analysis')}
            {renderSection13AccountingGrid('System Administration View · Global Workstation Health')}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <SummaryCard title="FastAPI Server" value="Healthy" change="HTTP 200 OK" isPositive={true} icon={Server} description="Port 8000 responding in 2.1ms" />
              <SummaryCard title="GPU VRAM Reserved" value="220 MB" change="4.6% of 4GB" isPositive={true} icon={Zap} description="NVIDIA GeForce RTX 2050" />
              <SummaryCard title="Platform Accounts" value="5 Users" change="5 Active" isPositive={true} icon={ShieldCheck} description="Role-Based Access Control" />
              <SummaryCard title="Audit Security Score" value="100%" change="Zero Breaches" isPositive={true} icon={Activity} description="HIPAA de-identification active" />
            </div>
          </div>
        ) : (
          /* =========================================================================
             FLAGSHIP: ALL-INCLUSIVE MASTER DEVELOPER DASHBOARD
             ========================================================================= */
          <div className="space-y-8">
            {/* Section 13 Core Case Accounting Grid */}
            {renderSection13AccountingGrid()}

            {/* Row 1: Deep Learning Engine & 5-Tier Severity Distribution */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* ML Loss Convergence */}
              <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-[#A91121]" />
                    <h4 className="text-sm font-bold text-[#252525]">Model Training Performance: Attention U-Net & Faster R-CNN</h4>
                  </div>
                  <span className="text-[11px] font-mono font-bold text-[#A91121] bg-red-50 px-2 py-0.5 rounded border border-red-200">
                    30 Epochs
                  </span>
                </div>
                <div className="h-64">
                  <Line data={trainingLossData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
                <div className="grid grid-cols-3 gap-2 pt-2 text-center text-xs border-t border-slate-100">
                  <div className="p-2 bg-slate-50 rounded">
                    <div className="text-[10px] text-slate-500 font-mono">Attention Dice</div>
                    <div className="font-bold text-blue-700 font-mono">0.6833</div>
                  </div>
                  <div className="p-2 bg-slate-50 rounded">
                    <div className="text-[10px] text-slate-500 font-mono">Faster R-CNN mAP</div>
                    <div className="font-bold text-emerald-700 font-mono">0.5840</div>
                  </div>
                  <div className="p-2 bg-slate-50 rounded">
                    <div className="text-[10px] text-slate-500 font-mono">%DS MAE</div>
                    <div className="font-bold text-[#A91121] font-mono">9.54%</div>
                  </div>
                </div>
              </div>

              {/* 5-Tier Severity Distribution Chart (Section 13) */}
              <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <BarChart2 className="w-4 h-4 text-[#A91121]" />
                    <h4 className="text-sm font-bold text-[#252525]">Stenosis Severity Distribution</h4>
                  </div>
                  <span className="text-[11px] font-mono font-bold text-[#A91121] bg-red-50 px-2 py-0.5 rounded border border-red-200">
                    1,514 Total Cases
                  </span>
                </div>
                <div className="h-64">
                  <Bar data={severityBarData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
                <div className="grid grid-cols-5 gap-1.5 text-center text-[10px] pt-2 border-t border-slate-100 font-mono">
                  <div className="p-1 bg-emerald-50 text-emerald-800 rounded font-bold">Normal: 312</div>
                  <div className="p-1 bg-blue-50 text-blue-800 rounded font-bold">Mild: 360</div>
                  <div className="p-1 bg-amber-50 text-amber-800 rounded font-bold">Mod: 482</div>
                  <div className="p-1 bg-rose-50 text-rose-800 rounded font-bold">Sev: 285</div>
                  <div className="p-1 bg-red-100 text-red-900 rounded font-bold">Crit: 75</div>
                </div>
              </div>
            </div>

            {/* Row 2: Research Cohorts & Artery Lesions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <Stethoscope className="w-4 h-4 text-[#A91121]" />
                    <h4 className="text-sm font-bold text-[#252525]">Coronary Lesion Territory Distribution (AHA Mapping)</h4>
                  </div>
                  <span className="text-[11px] font-mono font-bold text-[#A91121] bg-red-50 px-2 py-0.5 rounded border border-red-200">
                    27 Flagged Lesions
                  </span>
                </div>
                <div className="h-64">
                  <Bar data={radBarData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>

              <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                    <h4 className="text-sm font-bold text-[#252525]">Inter-Observer Consensus & Agreement Breakdown</h4>
                  </div>
                  <span className="text-[11px] font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    98.4% Readiness
                  </span>
                </div>
                <div className="h-64 flex items-center justify-center">
                  <Doughnut data={studyDoughnutData} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>
            </div>

            {/* Row 3: Section 13 Recent Analyses & Processing Status Queue */}
            {renderRecentAnalysesTable('Recent AI Diagnostic Analyses & Processing Queue', 'Real-time patient scans queued for quantitative QCA morphometry, Grad-CAM saliency proofs, and clinical sign-off')}

            {/* Row 4: Platform User Directory Snapshot */}
            <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-[#A91121]/15 pb-3">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-slate-700" />
                  <h4 className="text-sm font-bold text-[#252525]">Platform Access & Active User Accounts</h4>
                </div>
                <button
                  onClick={() => onNavigate('users')}
                  className="text-xs text-[#A91121] font-semibold hover:underline flex items-center gap-1"
                >
                  Manage Users & Roles <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                {INITIAL_USERS.map((u) => (
                  <div key={u.id} className="p-3 rounded-lg border border-[#A91121]/20 bg-slate-50/70 space-y-1.5">
                    <div className="flex items-center gap-2">
                      <UserAvatar role={u.role} size="sm" />
                      <div className="min-w-0 flex-1">
                        <div className="font-bold text-xs text-slate-900 truncate">{u.name}</div>
                        <div className="text-[10px] font-mono text-slate-500 truncate">{u.email}</div>
                      </div>
                    </div>
                    <div className="pt-1 flex items-center justify-between border-t border-[#A91121]/15">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                        u.role === 'Developer' ? 'bg-amber-100 text-amber-800 border-amber-300' :
                        u.role === 'Radiologist / Clinician' ? 'bg-red-50 text-red-700 border-red-200' :
                        u.role === 'Medical Researcher' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                        u.role === 'Data Scientist' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                        'bg-slate-100 text-slate-700 border-slate-300'
                      }`}>
                        {u.role.split(' ')[0]}
                      </span>
                      <span className="text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Active
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // =========================================================================
  // 1. MEDICAL RESEARCHER AI ANALYSIS DASHBOARD (Prof. David Chen)
  // =========================================================================
  if (currentUser.role === 'Medical Researcher') {
    return (
      <div className="space-y-6">
        <div className="bg-purple-50/70 border border-purple-200 rounded-xl p-4 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-purple-950">AI Cohort Analysis & Clinical Research Dashboard</h2>
            <p className="text-xs text-purple-800">Multi-center clinical trial progress and cohort consensus audit (Section 13 Protocol)</p>
          </div>
          <span className="text-xs font-mono font-bold px-2.5 py-1 bg-purple-600 text-white rounded-lg shadow-sm">
            Study Audit: 98.4% Readiness
          </span>
        </div>

        {/* Section 13 Accounting Grid */}
        {renderSection13AccountingGrid('Medical Research Cohort · ARCADE Trial')}

        {/* Cohort Enrollment & Severity Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-[#252525] mb-4">Study Cohort Enrollment Distribution</h3>
            <div className="h-64">
              <Bar data={studyBarData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-[#252525] mb-4">Inter-Observer Consensus Breakdown</h3>
            <div className="h-64 flex items-center justify-center">
              <Doughnut data={studyDoughnutData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>
        </div>

        {/* Section 13 Recent Analyses */}
        {renderRecentAnalysesTable('Cohort Study Repository & Annotation Queue', 'Multi-center clinical trial cohort consensus audit across 1,514 angiograms')}
      </div>
    );
  }

  // =========================================================================
  // 2. RADIOLOGIST / CLINICIAN AI ANALYSIS DASHBOARD (Dr. Aris Thorne)
  // =========================================================================
  if (currentUser.role === 'Radiologist / Clinician') {
    return (
      <div className="space-y-6">
        {/* Urgent Clinical Alert */}
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3 shadow-sm">
          <AlertTriangle className="w-5 h-5 text-[#A91121] shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <div className="font-bold text-[#A91121] flex items-center gap-2">
              <span>High-Risk Lesion Flagged for Urgent Clinical Triage</span>
              <span className="font-mono bg-red-100 text-red-800 px-1.5 py-0.2 rounded text-[10px]">CASE-1035</span>
            </div>
            <div className="text-slate-700">
              Patient Marcus Sterling (55y) presents with <strong>78.4% RCA proximal narrowing (MLD 0.50 mm)</strong>. FFR/iFR evaluation recommended.
            </div>
          </div>
          <button
            onClick={() => onNavigate('case-detail', 'CASE-1035')}
            className="ml-auto px-3 py-1.5 bg-[#A91121] hover:bg-[#800D1B] text-white text-xs font-semibold rounded-lg shrink-0 shadow-sm"
          >
            Review Now
          </button>
        </div>

        {/* Section 13 Accounting Grid */}
        {renderSection13AccountingGrid('Clinical Decision Support Worklist · 1,514 Total Cases')}

        {/* Dual Charts: 5-Tier Severity & Artery Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-[#252525] mb-4">Stenosis Severity Distribution</h3>
            <div className="h-64">
              <Bar data={severityBarData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-[#252525] mb-4">Artery Lesion Territory Distribution (AHA Mapping)</h3>
            <div className="h-64">
              <Bar data={radBarData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>
        </div>

        {/* Section 13 Recent Analyses Table */}
        {renderRecentAnalysesTable('Patient Diagnostic Reading Worklist', 'Active angiograms queued for quantitative QCA morphometry, Grad-CAM verification, and clinical sign-off')}
      </div>
    );
  }

  // =========================================================================
  // 3. DATA SCIENTIST AI ANALYSIS DASHBOARD (Dr. Helena Rostova)
  // =========================================================================
  if (currentUser.role === 'Data Scientist') {
    return (
      <div className="space-y-6">
        <div className="bg-red-50/40 border border-red-200/70 rounded-xl p-4 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-[#252525]">AI Model Performance & Neural Evaluation Hub</h2>
            <p className="text-xs text-slate-600">PyTorch CUDA engine · ResNet-18 Severity Network, Attention U-Net & Grad-CAM layer hooks</p>
          </div>
          <span className="text-xs font-mono font-bold px-2.5 py-1 bg-[#A91121] text-white rounded-lg shadow-sm">
            GPU: RTX 2050 (29.8 FPS)
          </span>
        </div>

        {/* Section 13 Accounting Grid */}
        {renderSection13AccountingGrid('Model Performance Telemetry · 1,514 Test & Validation Scans')}

        {/* Loss Convergence & 5-Tier Detection Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-[#252525] mb-4">Training Loss Convergence: Attention U-Net & Faster R-CNN</h3>
            <div className="h-64">
              <Line data={trainingLossData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>
          <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-[#252525] mb-4">5-Tier Severity Detection Distribution</h3>
            <div className="h-64 flex items-center justify-center">
              <Doughnut data={severityDoughnutData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>
        </div>

        {/* Section 13 Recent Analyses Table */}
        {renderRecentAnalysesTable('Model Benchmark Validation Queue', 'Real-time neural inference testing and calibrated confidence scores across benchmark angiograms')}
      </div>
    );
  }

  // =========================================================================
  // 4. ADMINISTRATOR AI ANALYSIS DASHBOARD (Sophia Martinez)
  // =========================================================================
  return (
    <div className="space-y-6">
      <div className="bg-red-50/40 border border-[#A91121]/20 rounded-xl p-4 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-900">System Administration & Analysis Pipeline Telemetry</h2>
          <p className="text-xs text-slate-600">Infrastructure health, GPU VRAM monitoring, and RBAC user provisioning (Section 13 Protocol)</p>
        </div>
        <span className="text-xs font-mono font-bold px-2.5 py-1 bg-[#A91121] text-white rounded-lg shadow-sm">
          System Status: Operational
        </span>
      </div>

      {/* Section 13 Accounting Grid */}
      {renderSection13AccountingGrid('Global System Throughput · 1,514 Total Cases')}

      {/* Admin Hardware Telemetry */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="FastAPI Server"
          value="Healthy"
          change="HTTP 200 OK"
          isPositive={true}
          icon={Server}
          description="Port 8000 responding in 2.1ms"
        />
        <SummaryCard
          title="GPU VRAM Reserved"
          value="220 MB"
          change="4.6% of 4GB"
          isPositive={true}
          icon={Zap}
          description="NVIDIA GeForce RTX 2050"
        />
        <SummaryCard
          title="Platform Accounts"
          value="5 Users"
          change="5 Active"
          isPositive={true}
          icon={ShieldCheck}
          description="Role-Based Access Control"
        />
        <SummaryCard
          title="Audit Security Score"
          value="100%"
          change="Zero Breaches"
          isPositive={true}
          icon={Activity}
          description="HIPAA de-identification active"
        />
      </div>

      {/* Admin Server Diagnostics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-[#252525] flex items-center gap-2">
            <Server className="w-4 h-4 text-[#A91121]" /> Server & Microservice Diagnostics
          </h3>
          <div className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-[#A91121]/20">
              <span className="font-mono font-semibold text-slate-700">FastAPI REST Server (:8000)</span>
              <span className="font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-bold border border-emerald-200">200 OK (2.1ms)</span>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-[#A91121]/20">
              <span className="font-mono font-semibold text-slate-700">Next.js Web Workstation (:3000)</span>
              <span className="font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-bold border border-emerald-200">Production Build</span>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-[#A91121]/20">
              <span className="font-mono font-semibold text-slate-700">PostgreSQL / Local Relational DB</span>
              <span className="font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-bold border border-emerald-200">Connected</span>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-[#A91121]/20">
              <span className="font-mono font-semibold text-slate-700">Storage Partitions (/raw, /masks, /xai, /reports)</span>
              <span className="font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-bold border border-emerald-200">Healthy (4.2 GB)</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-[#A91121]/20 rounded-xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#252525] flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#A91121]" /> Active RBAC User Accounts
            </h3>
            <button onClick={() => onNavigate('users')} className="text-xs text-[#A91121] hover:underline font-semibold">
              Manage Users
            </button>
          </div>
          <div className="space-y-2 text-xs">
            {INITIAL_USERS.map((u) => (
              <div key={u.id} className="p-2.5 bg-slate-50 rounded-lg flex items-center justify-between border border-[#A91121]/20">
                <div className="flex items-center gap-2.5 min-w-0">
                  <UserAvatar role={u.role} size="sm" />
                  <div className="min-w-0">
                    <div className="font-bold text-slate-800 truncate">{u.name}</div>
                    <div className="text-[11px] text-slate-500 font-mono truncate">{u.email}</div>
                  </div>
                </div>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                  u.role === 'Developer' ? 'bg-amber-100 text-amber-800 border-amber-300' :
                  u.role === 'Radiologist / Clinician' ? 'bg-red-50 text-red-700 border-red-200' :
                  u.role === 'Medical Researcher' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                  u.role === 'Data Scientist' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                  'bg-slate-100 text-slate-700 border-slate-300'
                }`}>
                  {u.role.split(' ')[0]}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
