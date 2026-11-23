'use client';

import React, { useState, useMemo } from 'react';
import Image from 'next/image';
import { MedicalCase, INITIAL_CASES } from '@/lib/mockData';
import {
  Search,
  LayoutGrid,
  List,
  Eye,
  FileText,
  MoreHorizontal,
  Calendar,
  User,
  ClipboardList,
  UploadCloud,
  FileSpreadsheet,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Layers,
  CheckSquare,
  Square,
  ArrowUpRight,
  ShieldAlert,
  ShieldCheck
} from 'lucide-react';
import { SystemUser } from '@/lib/mockData';
import { getCaseAccessMode } from '@/lib/permissions';

interface CaseManagementScreenProps {
  onNavigate: (screen: string, caseId?: string) => void;
  currentUser?: SystemUser;
}

export const CaseManagementScreen: React.FC<CaseManagementScreenProps> = ({ onNavigate, currentUser }) => {
  const [cases] = useState<MedicalCase[]>(INITIAL_CASES);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [worklistTab, setWorklistTab] = useState<'all' | 'reported' | 'review'>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [vesselFilter, setVesselFilter] = useState<string>('all');
  const [dateFilter, setDateFilter] = useState<string>('any');
  const [sortBy, setSortBy] = useState<string>('date_desc');
  const [modalityFilter, setModalityFilter] = useState<'all' | '2d' | '3d'>('all');

  const accessMode = getCaseAccessMode(currentUser?.role);
  const formatPatientName = (c: MedicalCase) =>
    accessMode === 'research-deidentified'
      ? `ANON-${c.id.replace(/[^0-9]/g, '') || '1010'} [De-Identified]`
      : c.patientName;

  // Dynamic counts for faceted sub-sidebar
  const counts = useMemo(() => {
    return {
      all: cases.length,
      reported: cases.filter((c) => c.status === 'Completed').length,
      review: cases.filter((c) => c.status === 'Pending Review').length,
      normal: cases.filter((c) => c.severityCategory === 'Normal').length,
      mild: cases.filter((c) => c.severityCategory === 'Mild').length,
      moderate: cases.filter((c) => c.severityCategory === 'Moderate').length,
      severe: cases.filter((c) => c.severityCategory === 'Severe').length,
      critical: cases.filter((c) => c.severityCategory === 'Critical').length,
      lad: cases.filter((c) => c.primaryVessel === 'LAD').length,
      rca: cases.filter((c) => c.primaryVessel === 'RCA').length,
      lcx: cases.filter((c) => c.primaryVessel === 'LCx').length,
      lm: cases.filter((c) => c.primaryVessel === 'LM').length,
      modality_2d: cases.filter((c) => !c.is3D).length,
      modality_3d: cases.filter((c) => !!c.is3D).length,
    };
  }, [cases]);

  // Dynamic severity theme generator for study card metrics strips
  const getSeverityTheme = (category: string) => {
    switch (category) {
      case 'Critical':
        return {
          container: 'bg-red-50/80 border-red-200 text-red-950',
          label: 'text-red-700/80',
          value: 'text-red-950 font-extrabold',
          badge: (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-bold rounded-full bg-[#8B0000] text-white border border-[#500000] shadow-2xs">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              <span>Critical</span>
            </span>
          ),
        };
      case 'Severe':
        return {
          container: 'bg-rose-50/70 border-rose-200 text-rose-950',
          label: 'text-rose-700/80',
          value: 'text-rose-950 font-extrabold',
          badge: (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold rounded-full bg-rose-100 text-rose-700 border border-rose-300 shadow-2xs">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              <span>Severe</span>
            </span>
          ),
        };
      case 'Moderate':
        return {
          container: 'bg-amber-50/70 border-amber-200 text-amber-950',
          label: 'text-amber-700/80',
          value: 'text-amber-950 font-extrabold',
          badge: (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold rounded-full bg-amber-100 text-amber-800 border border-amber-300 shadow-2xs">
              <Clock className="w-3.5 h-3.5 shrink-0" />
              <span>Moderate</span>
            </span>
          ),
        };
      case 'Mild':
        return {
          container: 'bg-blue-50/70 border-blue-200 text-blue-950',
          label: 'text-blue-700/80',
          value: 'text-blue-950 font-extrabold',
          badge: (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-700 border border-blue-300 shadow-2xs">
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
              <span>Mild</span>
            </span>
          ),
        };
      case 'Normal':
      default:
        return {
          container: 'bg-emerald-50/70 border-emerald-200 text-emerald-950',
          label: 'text-emerald-700/80',
          value: 'text-emerald-950 font-extrabold',
          badge: (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-700 border border-emerald-300 shadow-2xs">
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
              <span>Normal</span>
            </span>
          ),
        };
    }
  };

  // Filtering and sorting
  const filteredCases = useMemo(() => {
    return cases
      .filter((c) => {
        // Search filter
        const matchesSearch =
          c.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
          c.patientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
          c.patientId.toLowerCase().includes(searchQuery.toLowerCase()) ||
          c.researcher.toLowerCase().includes(searchQuery.toLowerCase()) ||
          c.primaryVessel.toLowerCase().includes(searchQuery.toLowerCase());

        // Worklist tab filter
        let matchesWorklist = true;
        if (worklistTab === 'reported') {
          matchesWorklist = c.status === 'Completed';
        } else if (worklistTab === 'review') {
          matchesWorklist = c.status === 'Pending Review';
        }

        // Severity filter
        const matchesSeverity =
          severityFilter === 'all' ||
          c.severityCategory.toLowerCase() === severityFilter.toLowerCase();

        // Vessel filter
        const matchesVessel =
          vesselFilter === 'all' ||
          c.primaryVessel.toLowerCase() === vesselFilter.toLowerCase();

        // Modality filter
        let matchesModality = true;
        if (modalityFilter === '2d') {
          matchesModality = !c.is3D;
        } else if (modalityFilter === '3d') {
          matchesModality = !!c.is3D;
        }

        return matchesSearch && matchesWorklist && matchesSeverity && matchesVessel && matchesModality;
      })
      .sort((a, b) => {
        if (sortBy === 'stenosis_desc') {
          return b.maxStenosisPercent - a.maxStenosisPercent;
        }
        if (sortBy === 'name_asc') {
          return a.patientName.localeCompare(b.patientName);
        }
        // Default: date_desc
        return new Date(b.uploadDate).getTime() - new Date(a.uploadDate).getTime();
      });
  }, [cases, searchQuery, worklistTab, severityFilter, vesselFilter, modalityFilter, sortBy]);

  const handleExportCohortCsv = () => {
    try {
      const headers = ['Case ID', 'Patient Name', 'Patient ID', 'Age', 'Gender', 'Modality', 'Primary Vessel', 'Stenosis %', 'Severity', 'Status', 'Study Date'];
      const rows = filteredCases.map(c => [
        `"${c.id}"`,
        `"${c.patientName}"`,
        `"${c.patientId}"`,
        c.age,
        `"${c.gender}"`,
        `"${c.is3D ? '3D CT' : '2D XCA'}"`,
        `"${c.primaryVessel}"`,
        `"${c.maxStenosisPercent}%"`,
        `"${c.severityCategory}"`,
        `"${c.status}"`,
        `"${c.uploadDate}"`
      ]);
      const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', `stenovision_cohort_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch {
      window.open('http://127.0.0.1:8000/api/v1/reports/export/csv', '_blank');
    }
  };

  return (
    <div className="relative bg-white border border-[#A91121]/20 rounded-2xl shadow-sm font-sans text-slate-800">
      {/* 1. STICKY TOP FILTER & ACTION TOOLBAR */}
      <div className="sticky -top-8 z-20 px-6 py-3 bg-[#F9FAFB] border-b border-[#A91121]/15 rounded-t-2xl flex flex-wrap items-center justify-between gap-2.5 shadow-xs">
        {/* Left: Search input */}
        <div className="relative flex-1 min-w-[220px] max-w-sm">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by Case ID, Patient ID, or Name..."
            className="w-full pl-9 pr-3 py-1.5 bg-white border border-[#A91121]/20 rounded-lg text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-[#A91121] focus:ring-1 focus:ring-[#A91121] transition-colors shadow-2xs"
          />
        </div>

        {/* Center & Right: Filter Dropdowns, View Mode Switcher & Export */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Study Date Dropdown */}
          <div className="relative">
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="appearance-none bg-white border border-[#A91121]/20 text-slate-700 rounded-lg pl-3 pr-8 py-1.5 focus:outline-none focus:border-[#A91121] cursor-pointer shadow-2xs"
            >
              <option value="any">Study Date: Any</option>
              <option value="today">Study Date: Today</option>
              <option value="week">Study Date: This Week</option>
              <option value="month">Study Date: This Month</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Modality Dropdown */}
          <div className="relative">
            <select
              value={modalityFilter}
              onChange={(e) => setModalityFilter(e.target.value as 'all' | '2d' | '3d')}
              className="appearance-none bg-white border border-[#A91121]/20 text-slate-700 rounded-lg pl-3 pr-8 py-1.5 focus:outline-none focus:border-[#A91121] cursor-pointer shadow-2xs font-semibold"
            >
              <option value="all">Modality: All ({counts.all})</option>
              <option value="2d">2D XCA Angiography ({counts.modality_2d})</option>
              <option value="3d">3D CT Volumetric ({counts.modality_3d})</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Sort Dropdown */}
          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="appearance-none bg-white border border-[#A91121]/20 text-slate-700 rounded-lg pl-3 pr-8 py-1.5 focus:outline-none focus:border-[#A91121] cursor-pointer shadow-2xs"
            >
              <option value="date_desc">Sort: Study Date ↓</option>
              <option value="stenosis_desc">Sort: % Stenosis ↓</option>
              <option value="name_asc">Sort: Patient Name A-Z</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* View Mode Switcher (Grid vs List) */}
          <div className="flex bg-slate-200/70 p-0.5 rounded-lg border border-[#A91121]/20">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded transition-all ${
                viewMode === 'grid'
                  ? 'bg-white text-[#A91121] shadow-xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
              title="Grid View (Workstation Cards)"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded transition-all ${
                viewMode === 'table'
                  ? 'bg-white text-[#A91121] shadow-xs font-semibold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
              title="Table View (Data List)"
            >
              <List className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Export CSV Button */}
          <button
            onClick={handleExportCohortCsv}
            className="px-3.5 py-1.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-[#A91121]/20 rounded-lg transition-colors inline-flex items-center gap-1.5 shadow-2xs hover:text-[#A91121]"
            title="Export Active Cohort to CSV"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-[#A91121]" /> Export CSV
          </button>
        </div>
      </div>

      {/* Access Mode Notification Banner */}
      {accessMode === 'research-deidentified' && (
        <div className="mx-6 mt-3 p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-between text-xs text-purple-900">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-purple-700 shrink-0" />
            <span><strong>Research Cohort Repository (De-Identified View)</strong> — Patient identifiers are masked in compliance with HIPAA Safe Harbor regulations.</span>
          </div>
          <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-purple-200 text-purple-800 shrink-0">HIPAA Safe Harbor</span>
        </div>
      )}
      {accessMode === 'benchmark-only' && (
        <div className="mx-6 mt-3 p-3 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-between text-xs text-blue-900">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-700 shrink-0" />
            <span><strong>Benchmark Dataset Explorer</strong> — Controlled clinical access to ARCADE (2D XCA) and PARSE (3D CCTA) validation cohorts.</span>
          </div>
          <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-blue-200 text-blue-800 shrink-0">Benchmark Mode</span>
        </div>
      )}
      {accessMode === 'audit-only' && (
        <div className="mx-6 mt-3 p-3 rounded-xl bg-slate-100 border border-slate-300 flex items-center justify-between text-xs text-slate-800">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-slate-600 shrink-0" />
            <span><strong>Clinical File Audit &amp; Archival Registry</strong> — System audit oversight mode. Medical cases are displayed for integrity verification.</span>
          </div>
          <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-slate-200 text-slate-800 shrink-0">Audit Mode</span>
        </div>
      )}

      {/* 2. TWO-COLUMN WORKSTATION LAYOUT */}
      <div className="flex flex-col md:flex-row items-start min-h-[580px]">
        {/* LEFT SUB-SIDEBAR: WORKLISTS & FACETED FILTERS */}
        <aside className="w-full md:w-60 bg-[#F9FAFB] border-b md:border-b-0 md:border-r border-[#A91121]/15 p-4 flex flex-col justify-between shrink-0 select-none md:sticky md:top-[28px] md:self-start md:max-h-[calc(100vh-140px)] md:overflow-y-auto rounded-bl-2xl">
          <div className="space-y-6">
            {/* Worklists Section */}
            <div>
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 px-1">
                Worklists
              </div>
              <div className="space-y-1 text-xs">
                <button
                  onClick={() => setWorklistTab('all')}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl font-medium transition-colors ${
                    worklistTab === 'all'
                      ? 'bg-[#A91121]/8 text-[#A91121] font-semibold border border-[#A91121]/30 shadow-2xs'
                      : 'text-slate-700 hover:bg-white hover:text-slate-900 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Layers className="w-3.5 h-3.5 text-[#A91121]" />
                    <span>All Studies</span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.2 rounded-full ${
                      worklistTab === 'all'
                        ? 'bg-[#A91121] text-white font-bold'
                        : 'bg-slate-200/80 text-slate-700 border border-slate-300/50'
                    }`}
                  >
                    {counts.all}
                  </span>
                </button>

                {/* 2. Reported */}
                <button
                  onClick={() => setWorklistTab('reported')}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl font-medium transition-colors ${
                    worklistTab === 'reported'
                      ? 'bg-[#A91121]/8 text-[#A91121] font-semibold border border-[#A91121]/30 shadow-2xs'
                      : 'text-slate-700 hover:bg-white hover:text-slate-900 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Reported</span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.2 rounded-full ${
                      worklistTab === 'reported'
                        ? 'bg-[#A91121] text-white font-bold'
                        : 'bg-slate-200/80 text-slate-700 border border-slate-300/50'
                    }`}
                  >
                    {counts.reported}
                  </span>
                </button>

                {/* 3. To Be Reviewed */}
                <button
                  onClick={() => setWorklistTab('review')}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl font-medium transition-colors ${
                    worklistTab === 'review'
                      ? 'bg-[#A91121]/8 text-[#A91121] font-semibold border border-[#A91121]/30 shadow-2xs'
                      : 'text-slate-700 hover:bg-white hover:text-slate-900 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5 text-amber-500" />
                    <span>To Be Reviewed</span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.2 rounded-full ${
                      worklistTab === 'review'
                        ? 'bg-[#A91121] text-white font-bold'
                        : 'bg-slate-200/80 text-slate-700 border border-slate-300/50'
                    }`}
                  >
                    {counts.review}
                  </span>
                </button>
              </div>
            </div>

            {/* Faceted Filters Section */}
            <div>
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2.5 px-1">
                Filters
              </div>

              {/* Severity Checkboxes */}
              <div className="space-y-1 mb-4 text-xs">
                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1 px-1">
                  Severity
                </div>
                {[
                  { label: 'Normal', key: 'normal', count: counts.normal },
                  { label: 'Mild', key: 'mild', count: counts.mild },
                  { label: 'Moderate', key: 'moderate', count: counts.moderate },
                  { label: 'Severe', key: 'severe', count: counts.severe },
                  { label: 'Critical', key: 'critical', count: counts.critical },
                ].map((s) => {
                  const isChecked = severityFilter === s.key;
                  return (
                    <button
                      key={s.key}
                      onClick={() => setSeverityFilter(isChecked ? 'all' : s.key)}
                      className={`w-full flex items-center justify-between px-2 py-1 rounded transition-colors ${
                        isChecked ? 'bg-white shadow-2xs text-[#252525] font-semibold' : 'text-slate-600 hover:bg-white/70'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {isChecked ? (
                          <CheckSquare className="w-3.5 h-3.5 text-[#A91121]" />
                        ) : (
                          <Square className="w-3.5 h-3.5 text-slate-400" />
                        )}
                        <span>{s.label}</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">{s.count}</span>
                    </button>
                  );
                })}
              </div>

              {/* Primary Vessel Checkboxes */}
              <div className="space-y-1 text-xs">
                <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1 px-1">
                  Primary Vessel
                </div>
                {[
                  { label: 'LAD', key: 'LAD', count: counts.lad },
                  { label: 'RCA', key: 'RCA', count: counts.rca },
                  { label: 'LCx', key: 'LCx', count: counts.lcx },
                  { label: 'LM', key: 'LM', count: counts.lm },
                ].map((v) => {
                  const isChecked = vesselFilter === v.key;
                  return (
                    <button
                      key={v.key}
                      onClick={() => setVesselFilter(isChecked ? 'all' : v.key)}
                      className={`w-full flex items-center justify-between px-2 py-1 rounded transition-colors ${
                        isChecked ? 'bg-white shadow-2xs text-[#252525] font-semibold' : 'text-slate-600 hover:bg-white/70'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {isChecked ? (
                          <CheckSquare className="w-3.5 h-3.5 text-[#A91121]" />
                        ) : (
                          <Square className="w-3.5 h-3.5 text-slate-400" />
                        )}
                        <span>{v.label}</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">{v.count}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Import Study Action Button */}
          <div className="pt-4 border-t border-[#A91121]/15 mt-4">
            <button
              onClick={() => onNavigate('upload')}
              className="w-full py-2.5 px-3 border border-[#A91121] text-[#A91121] hover:bg-[#A91121]/5 bg-white rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-colors shadow-2xs"
            >
              <UploadCloud className="w-4 h-4 text-[#A91121]" />
              <span>Import Study (DICOM)</span>
            </button>
          </div>
        </aside>

        {/* CENTRAL STUDY CANVAS */}
        <main className="flex-1 p-5 bg-[#F9FAFB]/50 flex flex-col justify-between min-w-0 rounded-br-2xl">
          {filteredCases.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-slate-100 border border-[#A91121]/20 flex items-center justify-center text-slate-400">
                <Search className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-[#252525]">No Studies Match Your Criteria</h3>
              <p className="text-xs text-slate-500 max-w-sm">
                Try clearing active severity filters or searching with a different case ID or patient name.
              </p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSeverityFilter('all');
                  setVesselFilter('all');
                  setWorklistTab('all');
                }}
                className="px-3.5 py-1.5 bg-[#A91121] hover:bg-[#8B0E1B] text-white rounded-lg text-xs font-semibold transition-colors shadow-2xs"
              >
                Reset All Filters
              </button>
            </div>
          ) : viewMode === 'grid' ? (
            /* GRID VIEW: 3-COLUMN CLINICAL STUDY CARDS MATCHING TARGET MOCKUP */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredCases.map((c) => {
                const theme = getSeverityTheme(c.severityCategory);

                return (
                  <div
                    key={c.id}
                    className="bg-white border border-[#A91121]/20 hover:border-[#A91121]/50 rounded-xl p-4 flex flex-col justify-between transition-all shadow-xs hover:shadow-md group"
                  >
                    {/* Top Bar: Case ID & Scan Modality */}
                    <div className="flex items-center justify-between pb-2.5 border-b border-slate-100">
                      <span className="font-mono font-bold text-[#A91121] text-sm tracking-wide">{c.id}</span>
                      <div className="flex items-center gap-1.5">
                        {c.is3D && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded-full bg-cyan-100 text-cyan-800 border border-cyan-300 shadow-2xs font-mono">
                            <Layers className="w-2.5 h-2.5 text-cyan-600" />
                            3D CT ({c.totalSlices || 256} sl)
                          </span>
                        )}
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-50 text-slate-600 border border-[#A91121]/20 font-medium">
                          {c.is3D ? 'CTPA' : (c.scanType.includes('DICOM') ? 'DICOM' : 'XCA')}
                        </span>
                      </div>
                    </div>

                    {/* Demographics & Angiogram Scan Thumbnail */}
                    <div className="grid grid-cols-2 gap-3 py-3 items-center">
                      <div className="space-y-1.5 text-xs text-slate-600 min-w-0">
                        <div className="font-semibold text-[#252525] flex items-center gap-1.5 truncate">
                          <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          <span className="truncate">{formatPatientName(c)}</span>
                        </div>
                        <div className="text-[11px] font-mono text-slate-500 flex items-center gap-1.5 truncate">
                          <ClipboardList className="w-3 h-3 text-slate-400 shrink-0" />
                          <span className="truncate">{c.patientId} · {c.gender[0]} · {c.age}y</span>
                        </div>
                        <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
                          <Calendar className="w-3 h-3 text-slate-400 shrink-0" />
                          <span>{c.uploadDate.split(' ')[0]}</span>
                        </div>
                      </div>

                      {/* Angiogram Scan Viewport with Target Lesion Marker */}
                      <div
                        onClick={() => onNavigate('case-detail', c.id)}
                        className="relative w-full h-24 rounded-lg overflow-hidden bg-black border border-[#A91121]/20 cursor-pointer shadow-inner"
                        title="Click to Examine Study"
                      >
                        <Image
                          src={c.rawScanUrl || '/assets/cases/10.png'}
                          alt={c.id}
                          fill
                          className="object-cover group-hover:scale-105 transition-transform"
                        />
                        {/* Target lesion indicator matching mockup */}
                        <div className="absolute top-[48%] left-[54%] transform -translate-x-1/2 -translate-y-1/2 pointer-events-none">
                          <span className="text-cyan-400 text-xs font-bold drop-shadow-[0_0_4px_rgba(34,211,238,0.9)] animate-pulse">
                            ▶
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Dynamic Color-Tinted Metrics Strip (Severity Themed) */}
                    <div className={`grid grid-cols-3 gap-2 py-2 px-3 rounded-lg border ${theme.container} items-center my-1.5 text-center`}>
                      <div>
                        <div className={`text-[10px] uppercase font-mono ${theme.label}`}>Stenosis</div>
                        <div className={`text-sm font-bold font-mono ${theme.value}`}>{c.maxStenosisPercent}%</div>
                      </div>
                      <div>
                        <div className={`text-[10px] uppercase font-mono ${theme.label}`}>Vessel</div>
                        <div className={`text-sm font-bold font-mono ${theme.value}`}>{c.primaryVessel}</div>
                      </div>
                      <div>
                        <div className={`text-[10px] uppercase font-mono mb-0.5 ${theme.label}`}>Severity</div>
                        {theme.badge}
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center justify-between pt-2.5 border-t border-slate-100 gap-2">
                      <button
                        onClick={() => onNavigate('case-detail', c.id)}
                        className="flex-1 py-1.5 px-2 bg-white hover:bg-slate-50 text-[#252525] border border-[#A91121]/20 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-2xs hover:border-[#A91121]/40"
                      >
                        <Eye className="w-3.5 h-3.5 text-[#A91121]" /> Preview
                      </button>
                      <button
                        onClick={() => onNavigate('reports')}
                        className="flex-1 py-1.5 px-2 bg-white hover:bg-slate-50 text-slate-700 hover:text-[#A91121] border border-[#A91121]/20 text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5 shadow-2xs hover:border-[#A91121]/40"
                      >
                        <FileText className="w-3.5 h-3.5 text-slate-400" /> Report
                      </button>
                      <button
                        onClick={() => onNavigate('case-detail', c.id)}
                        className="p-1.5 bg-white hover:bg-slate-50 text-slate-400 hover:text-slate-700 border border-[#A91121]/20 rounded-lg transition-colors shadow-2xs"
                        title="More Options"
                      >
                        <MoreHorizontal className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            /* TABLE VIEW: CLEAN INTEGRATED STENOVISION DATA TABLE */
            <div className="bg-white border border-[#A91121]/20 rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50/80 border-b border-[#A91121]/15 font-mono text-slate-600 text-xs font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="p-3">CASE ID</th>
                    <th className="p-3">PATIENT NAME & ID</th>
                    <th className="p-3">SCAN TYPE</th>
                    <th className="p-3">PRIMARY VESSEL</th>
                    <th className="p-3">MAX STENOSIS</th>
                    <th className="p-3">SEVERITY</th>
                    <th className="p-3">DATE</th>
                    <th className="p-3 text-right">ACTIONS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredCases.map((c) => {
                    const theme = getSeverityTheme(c.severityCategory);

                    return (
                      <tr
                        key={c.id}
                        onClick={() => onNavigate('case-detail', c.id)}
                        className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                      >
                        <td className="p-3 font-mono font-bold text-[#A91121]">{c.id}</td>
                        <td className="p-3">
                          <div className="font-semibold text-[#252525]">{formatPatientName(c)}</div>
                          <div className="text-[11px] font-mono text-slate-500">{accessMode === 'research-deidentified' ? 'De-Identified Subject' : `${c.patientId} · ${c.age}y / ${c.gender[0]}`}</div>
                        </td>
                        <td className="p-3 font-mono text-slate-600">
                          <div className="flex items-center gap-1.5">
                            {c.is3D && (
                              <span className="px-2 py-0.5 rounded-full bg-cyan-100 text-cyan-800 border border-cyan-300 font-bold text-[10px] flex items-center gap-1">
                                <Layers className="w-2.5 h-2.5 text-cyan-600" />
                                3D CT
                              </span>
                            )}
                            <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-[#A91121]/20 font-medium">
                              {c.is3D ? 'CTPA' : (c.scanType.includes('DICOM') ? 'DICOM' : 'XCA')}
                            </span>
                          </div>
                        </td>
                        <td className="p-3 font-mono font-semibold text-slate-800">{c.primaryVessel}</td>
                        <td className="p-3 font-mono font-bold text-[#252525]">{c.maxStenosisPercent}%</td>
                        <td className="p-3">{theme.badge}</td>
                        <td className="p-3 font-mono text-slate-500 text-[11px]">{c.uploadDate}</td>
                        <td className="p-3 text-right">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onNavigate('case-detail', c.id);
                            }}
                            className="px-2.5 py-1 text-xs font-semibold text-[#A91121] bg-[#A91121]/10 hover:bg-[#A91121]/20 rounded-md transition-colors inline-flex items-center gap-1 border border-[#A91121]/20"
                          >
                            Details <ArrowUpRight className="w-3 h-3" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* 4. FOOTER: RECORD COUNT & PAGINATION */}
          <div className="pt-4 border-t border-[#A91121]/15 mt-5 flex items-center justify-between text-xs text-slate-500 font-mono">
            <span>
              Showing 1 – {filteredCases.length} of {filteredCases.length} studies
            </span>

            <div className="flex items-center gap-1.5">
              <button
                disabled
                className="p-1 rounded bg-slate-100 text-slate-400 border border-[#A91121]/20 cursor-not-allowed opacity-50"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-2.5 py-0.5 rounded bg-[#A91121] text-white font-bold text-xs">
                1
              </span>
              <button
                disabled
                className="p-1 rounded bg-slate-100 text-slate-400 border border-[#A91121]/20 cursor-not-allowed opacity-50"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};
