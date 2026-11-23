'use client';

import React, { useState, useEffect } from 'react';
import { INITIAL_REPORTS, AnalysisReport, INITIAL_CASES, SystemUser } from '@/lib/mockData';
import { canGenerateReports } from '@/lib/permissions';
import { DataTable, Column } from '../DataTable';
import { SummaryCard } from '../SummaryCard';
import { ReportDetailModal } from '../ReportDetailModal';
import {
  FileText,
  Download,
  Plus,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileSpreadsheet,
  FileCode,
  Eye,
  Filter,
  Search,
  Check,
  ShieldCheck,
  Activity,
  Layers,
  X,
  Cpu
} from 'lucide-react';
import {
  fetchReports,
  generateReport,
  downloadReportPdf,
  exportReportJson,
  exportCohortCsv,
  toggleReportSignOff
} from '@/lib/api';

interface ReportsScreenProps {
  onNavigate: (screen: string) => void;
  currentUser?: SystemUser;
}

export const ReportsScreen: React.FC<ReportsScreenProps> = ({ onNavigate, currentUser }) => {
  const [reports, setReports] = useState<AnalysisReport[]>(INITIAL_REPORTS);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedReport, setSelectedReport] = useState<AnalysisReport | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isExportingCsv, setIsExportingCsv] = useState<boolean>(false);
  const [showGenerateModal, setShowGenerateModal] = useState<boolean>(false);
  const [targetCaseId, setTargetCaseId] = useState<string>('CASE-1010');

  // Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    loadReports();
  }, [severityFilter, statusFilter]);

  const loadReports = async () => {
    setLoading(true);
    try {
      const data = await fetchReports({
        severity: severityFilter,
        status: statusFilter,
        search: searchQuery
      });
      setReports(data);
    } catch (err) {
      console.error('Failed to load reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadReports();
  };

  const handleOpenDetail = (report: AnalysisReport) => {
    setSelectedReport(report);
    setIsModalOpen(true);
  };

  const handleDownloadPdf = async (report: AnalysisReport) => {
    await downloadReportPdf(report.reportId);
  };

  const handleExportJson = async (report: AnalysisReport) => {
    await exportReportJson(report);
  };

  const handleExportCsv = async () => {
    setIsExportingCsv(true);
    try {
      await exportCohortCsv();
    } finally {
      setIsExportingCsv(false);
    }
  };

  const handleToggleSign = async (report: AnalysisReport) => {
    try {
      const updated = await toggleReportSignOff(report.reportId);
      setReports((prev) => prev.map((r) => (r.reportId === updated.reportId ? updated : r)));
      if (selectedReport?.reportId === updated.reportId) {
        setSelectedReport(updated);
      }
    } catch (err) {
      console.error('Sign-off toggle error:', err);
    }
  };

  const handleGenerateNewReport = async () => {
    setIsGenerating(true);
    try {
      const newReport = await generateReport(targetCaseId);
      setReports((prev) => [newReport, ...prev.filter((r) => r.reportId !== newReport.reportId)]);
      setShowGenerateModal(false);
      handleOpenDetail(newReport);
    } catch (err) {
      console.error('Failed to generate report:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  // KPI Calculations
  const totalCount = reports.length;
  const verifiedCount = reports.filter((r) => r.reviewStatus === 'Verified' || r.reviewStatus === 'Signed Off').length;
  const pendingCount = reports.filter((r) => r.reviewStatus === 'Pending Review').length;
  const criticalCount = reports.filter((r) => r.severityCategory === 'Critical' || r.reviewStatus === 'Urgent Review').length;

  const getSeverityBadgeClass = (category?: string) => {
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

  const columns: Column<AnalysisReport>[] = [
    {
      header: 'Report ID',
      accessorKey: 'reportId',
      className: 'font-mono font-semibold text-[#A91121] cursor-pointer hover:underline',
    },
    {
      header: 'Patient & Case',
      accessorKey: (row) => {
        const isResearcher = currentUser?.role === 'Medical Researcher';
        const displayPatient = isResearcher
          ? `ANON-${row.caseId.replace(/[^0-9]/g, '') || '1010'} [De-Identified]`
          : row.patientName;

        return (
          <div>
            <div className="font-semibold text-foreground flex items-center gap-1.5">
              <span>{displayPatient}</span>
              {row.is3D && (
                <span className="inline-flex items-center gap-0.5 px-1.5 py-0.2 text-[9px] font-bold rounded-full bg-cyan-100 text-cyan-800 border border-cyan-300">
                  <Layers className="w-2.5 h-2.5 text-cyan-600" /> 3D CT
                </span>
              )}
            </div>
            <div className="text-xs font-mono text-muted-foreground flex items-center gap-1.5">
              <span>{row.caseId}</span>
              {row.patientId && !isResearcher && <span>· {row.patientId}</span>}
            </div>
          </div>
        );
      },
    },
    {
      header: 'Target Vessel / Segment',
      accessorKey: (row) => (
        <div>
          <div className="text-xs font-medium text-foreground">{row.primaryVessel || 'Coronary Branch'}</div>
          <div className="text-[11px] text-muted-foreground">{row.ahaSegment || 'AHA Segment'}</div>
        </div>
      ),
    },
    {
      header: 'QCA Stenosis & MLD',
      accessorKey: (row) => (
        <div className="font-mono text-xs">
          <div className="font-bold text-foreground">
            {row.pctStenosis !== undefined ? `${row.pctStenosis.toFixed(1)}% DS` : row.consensusScore}
          </div>
          <div className="text-[11px] text-muted-foreground">
            MLD: {row.mldMm !== undefined ? `${row.mldMm.toFixed(2)} mm` : '0.50 mm'}
          </div>
        </div>
      ),
    },
    {
      header: 'ACC/AHA Severity',
      accessorKey: (row) => (
        <span className={`inline-block px-2.5 py-0.5 text-xs font-semibold rounded-full border ${getSeverityBadgeClass(row.severityCategory)}`}>
          {row.severityCategory || 'Moderate'}
        </span>
      ),
    },
    {
      header: 'Status & Signature',
      accessorKey: (row) => {
        const isVerified = row.reviewStatus === 'Verified' || row.reviewStatus === 'Signed Off';
        const isUrgent = row.reviewStatus === 'Urgent Review';
        return (
          <div className="text-xs">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-medium ${
              isVerified
                ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30'
                : isUrgent
                ? 'bg-red-500/10 text-red-700 dark:text-red-400 border border-red-500/30 animate-pulse'
                : 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30'
            }`}>
              {isVerified ? <Check className="w-3 h-3" /> : isUrgent ? <AlertTriangle className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
              {row.reviewStatus || 'Pending Review'}
            </span>
            {row.signedBy && (
              <div className="text-[10px] text-muted-foreground mt-0.5 truncate max-w-[130px]">
                {row.signedBy}
              </div>
            )}
          </div>
        );
      },
    },
    {
      header: 'Actions',
      accessorKey: (row) => (
        <div className="flex items-center justify-end gap-1.5">
          <button
            onClick={() => handleOpenDetail(row)}
            className="p-1.5 text-xs font-semibold text-secondary-foreground bg-secondary hover:bg-secondary/80 rounded-md transition-colors border border-border"
            title="Audit Full Clinical Report"
          >
            <Eye className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => handleDownloadPdf(row)}
            className="p-1.5 text-xs font-semibold text-[#A91121] bg-[#A91121]/10 hover:bg-[#A91121]/20 rounded-md transition-colors"
            title="Download Publication PDF"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => handleExportJson(row)}
            className="p-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground bg-muted hover:bg-muted/80 rounded-md transition-colors"
            title="Export JSON"
          >
            <FileCode className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => handleToggleSign(row)}
            className={`p-1.5 text-xs font-semibold rounded-md transition-colors ${
              row.reviewStatus === 'Verified' || row.reviewStatus === 'Signed Off' || row.reviewStatus === 'Approved'
                ? 'text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20'
                : 'text-amber-700 dark:text-amber-400 bg-amber-500/10 hover:bg-amber-500/20'
            }`}
            title={row.reviewStatus === 'Verified' || row.reviewStatus === 'Approved' ? 'Revoke Signature' : 'Quick Sign & Approve'}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
          </button>
        </div>
      ),
      className: 'text-right',
    },
  ];

  return (
    <div className="space-y-6">
      
      {/* Title & Action Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <FileText className="w-5 h-5 text-[#A91121]" />
            {currentUser?.role === 'Medical Researcher'
              ? 'Publication Reports & Clinical Trials'
              : currentUser?.role === 'Administrator'
              ? 'Clinical Reports Audit & Verification Worklist'
              : 'Automated Clinical Diagnostic Reports'}
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            {currentUser?.role === 'Medical Researcher'
              ? 'Cohort QCA statistical summaries, anonymized trial outcomes, and multi-format CSV/JSON epidemiological exports.'
              : currentUser?.role === 'Administrator'
              ? 'System-wide HIPAA audit logs, verification tracking, and archived diagnostic summaries.'
              : 'Publication-grade quantitative coronary angiography (QCA) summaries, multi-format exports (PDF, JSON, CSV), and physician sign-off (Clinical Reporting Protocol Section 14).'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCsv}
            disabled={isExportingCsv}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors border border-border shadow-sm disabled:opacity-50"
            title="Export full cohort analysis summary in tabular CSV format"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            {isExportingCsv ? 'Exporting CSV...' : 'Export Cohort (CSV)'}
          </button>

          {canGenerateReports(currentUser?.role) && (
            <button
              onClick={() => setShowGenerateModal(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-[#A91121] hover:bg-[#8B0E1B] rounded-lg transition-colors shadow-sm cursor-pointer"
            >
              <Plus className="w-4 h-4" /> Generate Clinical Report
            </button>
          )}
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          title="Total Reports Generated"
          value={totalCount}
          description="Archived QCA analyses"
          icon={FileText}
          isPositive={true}
        />
        <SummaryCard
          title="Verified & Signed Off"
          value={verifiedCount}
          change={`${Math.round((verifiedCount / (totalCount || 1)) * 100)}%`}
          description="Physician approved"
          icon={CheckCircle2}
          isPositive={true}
        />
        <SummaryCard
          title="Pending Clinical Review"
          value={pendingCount}
          description="Awaiting attending MD sign"
          icon={Clock}
          isPositive={false}
        />
        <SummaryCard
          title="Critical Lesion Alerts"
          value={criticalCount}
          change="TIMI 0/1 Flow"
          description="Urgent catheterization lab"
          icon={AlertTriangle}
          isPositive={false}
        />
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 rounded-lg bg-card border border-border">
        <form onSubmit={handleSearchSubmit} className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by Patient Name, Case ID (e.g. CASE-1010), or Target Vessel..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs rounded-md bg-background border border-border focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </form>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Filter className="w-3.5 h-3.5" />
            <span>Severity:</span>
          </div>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="text-xs py-1.5 px-2.5 rounded-md bg-background border border-border focus:outline-none"
          >
            <option value="all">All Severities</option>
            <option value="Normal">Normal (&lt;25%)</option>
            <option value="Mild">Mild (25-49%)</option>
            <option value="Moderate">Moderate (50-69%)</option>
            <option value="Severe">Severe (70-89%)</option>
            <option value="Critical">Critical (≥90%)</option>
          </select>

          <div className="flex items-center gap-1 text-xs text-muted-foreground ml-2">
            <span>Status:</span>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs py-1.5 px-2.5 rounded-md bg-background border border-border focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="Verified">Verified & Signed</option>
            <option value="Pending Review">Pending Review</option>
            <option value="Urgent Review">Urgent Review</option>
          </select>
        </div>
      </div>

      {/* Main Reports DataTable */}
      <DataTable
        data={reports}
        columns={columns}
        keyExtractor={(row) => row.reportId}
        pageSize={6}
      />

      {/* Detail & Audit Modal */}
      <ReportDetailModal
        report={selectedReport}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onReportUpdated={(updated) => {
          setReports((prev) => prev.map((r) => (r.reportId === updated.reportId ? updated : r)));
        }}
        currentUser={currentUser}
      />

      {/* Generate Report Quick Dialog */}
      {showGenerateModal && (() => {
        const selectedCase = INITIAL_CASES.find((c) => c.id === targetCaseId) || INITIAL_CASES[0];
        const is3D = Boolean(selectedCase.is3D || selectedCase.scanType?.includes('3D') || selectedCase.id.startsWith('PA'));

        return (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white border border-slate-200 rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden flex flex-col p-6 space-y-4">
              
              {/* Header Bar with Brand Icon & Close X */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-red-50 text-[#A91121]">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-[#252525] text-sm sm:text-base">Generate Clinical Diagnostic Report</h3>
                    <p className="text-xs text-slate-500">Select a coronary case to compile QCA morphometrics &amp; clinical findings</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
                  title="Close Dialog"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Study Selection Dropdown */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#252525] flex items-center justify-between">
                  <span>Target Coronary Case Study</span>
                  <span className="text-[10px] font-mono text-slate-400">{INITIAL_CASES.length} available studies</span>
                </label>
                <div className="relative">
                  <select
                    value={targetCaseId}
                    onChange={(e) => setTargetCaseId(e.target.value)}
                    className="w-full text-xs font-medium py-2.5 px-3 rounded-lg bg-white border border-slate-300 text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#A91121]/20 focus:border-[#A91121] transition-all cursor-pointer"
                  >
                    {INITIAL_CASES.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.id} — {c.patientName} ({c.is3D ? '3D CCTA Volumetric' : '2D XCA'}) • {c.primaryVessel} ({c.maxStenosisPercent}% DS)
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Dynamic Interactive Clinical Study Preview Card */}
              {selectedCase && (
                <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/80 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-slate-900 text-white">
                        {selectedCase.id}
                      </span>
                      <span className="font-bold text-xs text-slate-900">
                        {selectedCase.patientName}
                      </span>
                      <span className="text-[11px] text-slate-500">
                        ({selectedCase.age}y · {selectedCase.gender})
                      </span>
                    </div>
                    <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full border ${
                      is3D 
                        ? 'bg-cyan-500/10 text-cyan-700 border-cyan-500/30' 
                        : 'bg-indigo-500/10 text-indigo-700 border-indigo-500/30'
                    }`}>
                      {is3D ? '3D CT Volumetric' : '2D XCA Fluoroscopy'}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-1 border-t border-slate-200 text-center">
                    <div className="p-1.5 rounded-lg bg-white border border-slate-200">
                      <div className="text-[10px] text-slate-500 uppercase font-semibold">Target Vessel</div>
                      <div className="font-bold font-mono text-xs text-slate-900 mt-0.5">{selectedCase.primaryVessel}</div>
                    </div>
                    <div className="p-1.5 rounded-lg bg-white border border-slate-200">
                      <div className="text-[10px] text-slate-500 uppercase font-semibold">Stenosis (%DS)</div>
                      <div className="font-bold font-mono text-xs text-[#A91121] mt-0.5">{selectedCase.maxStenosisPercent}%</div>
                    </div>
                    <div className="p-1.5 rounded-lg bg-white border border-slate-200">
                      <div className="text-[10px] text-slate-500 uppercase font-semibold">Severity Tier</div>
                      <div className="font-bold text-[11px] text-slate-900 mt-0.5 truncate">{selectedCase.severityCategory || 'Assessed'}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Structured 4-Point Diagnostic Pipeline Scope Checklist */}
              <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/80 shadow-2xs space-y-2">
                <div className="text-[11px] font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-[#A91121]" />
                  Automated Diagnostic Pipeline Scope
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  <div className="flex items-center gap-2 text-slate-600">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Quantitative Caliper Profiling (MLD, RVD, %DS)</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-600">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Dual-View Artery Contours &amp; Localization</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-600">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Explainable AI Grad-CAM Saliency Proof</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-600">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>ACC/AHA Diagnostic Grading &amp; MD Sign-Off</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowGenerateModal(false)}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleGenerateNewReport}
                  disabled={isGenerating}
                  className="px-5 py-2 text-xs font-bold rounded-lg bg-[#A91121] text-white hover:bg-[#8B0E1B] transition-all flex items-center gap-2 shadow-sm disabled:opacity-50 cursor-pointer"
                >
                  {isGenerating ? (
                    <>
                      <Cpu className="w-4 h-4 animate-spin" />
                      <span>Compiling Diagnostic Report...</span>
                    </>
                  ) : (
                    <>
                      <FileText className="w-4 h-4" />
                      <span>Generate Diagnostic Report</span>
                    </>
                  )}
                </button>
              </div>

            </div>
          </div>
        );
      })()}

    </div>
  );
};
