export type UserRole =
  | 'Developer'
  | 'Radiologist / Clinician'
  | 'Medical Researcher'
  | 'Data Scientist'
  | 'Administrator';

export interface NavItemDef {
  id: string;
  label: string;
  iconName: 'LayoutDashboard' | 'FolderKanban' | 'Folder' | 'UploadCloud' | 'Sliders' | 'BarChart3' | 'FileText' | 'Users' | 'Cpu' | 'Activity' | 'ShieldAlert' | 'Microscope' | 'Terminal' | 'FileCheck' | 'Monitor';
  badge?: string;
}

export interface RoleConfig {
  roleTitle: string;
  badgeColor: string;
  homeScreen: string;
  allowedScreens: string[];
  navItems: NavItemDef[];
}

export const ROLE_CONFIGURATIONS: Record<UserRole, RoleConfig> = {
  'Developer': {
    roleTitle: 'Developer (Superuser)',
    badgeColor: 'bg-amber-50 text-amber-800 border-amber-300',
    homeScreen: 'dashboard',
    allowedScreens: ['dashboard', 'cases', 'upload', 'config', 'models', 'results', 'case-detail', 'reports', 'users'],
    navItems: [
      { id: 'dashboard', label: 'Dashboard', iconName: 'Monitor' },
      { id: 'cases', label: 'Cases', iconName: 'Folder' },
      { id: 'upload', label: 'Scan Upload', iconName: 'UploadCloud', badge: '512x512' },
      { id: 'config', label: 'Model Config', iconName: 'Sliders' },
      { id: 'models', label: 'Model Comparison', iconName: 'Cpu', badge: 'v1.0-v2.1' },
      { id: 'results', label: 'Analysis Results', iconName: 'BarChart3' },
      { id: 'reports', label: 'Reports & Activity', iconName: 'FileCheck' },
      { id: 'users', label: 'User Management', iconName: 'Users' },
    ],
  },
  'Radiologist / Clinician': {
    roleTitle: 'Radiologist / Clinician',
    badgeColor: 'bg-red-50 text-red-700 border-red-200',
    homeScreen: 'dashboard',
    allowedScreens: ['dashboard', 'cases', 'case-detail', 'upload', 'config', 'results', 'reports', 'models'],
    navItems: [
      { id: 'dashboard', label: 'Analysis Overview', iconName: 'LayoutDashboard', badge: 'Active AI' },
      { id: 'cases', label: 'Angiogram Cases', iconName: 'FolderKanban' },
      { id: 'upload', label: 'Scan Upload', iconName: 'UploadCloud', badge: '512x512' },
      { id: 'results', label: 'QCA & Grad-CAM', iconName: 'BarChart3' },
      { id: 'models', label: 'Model Comparison', iconName: 'Cpu', badge: 'v1.0-v2.1' },
      { id: 'reports', label: 'Clinical Reports', iconName: 'FileCheck' },
    ],
  },
  'Medical Researcher': {
    roleTitle: 'Medical Researcher',
    badgeColor: 'bg-purple-50 text-purple-700 border-purple-200',
    homeScreen: 'dashboard',
    allowedScreens: ['dashboard', 'cases', 'case-detail', 'upload', 'config', 'results', 'reports', 'users', 'models'],
    navItems: [
      { id: 'dashboard', label: 'Cohort Dashboard', iconName: 'LayoutDashboard', badge: '1,514 Cases' },
      { id: 'cases', label: 'Study Repository', iconName: 'FolderKanban' },
      { id: 'upload', label: 'Scan Upload', iconName: 'UploadCloud', badge: 'De-ID' },
      { id: 'results', label: 'Diagnostic Findings', iconName: 'BarChart3' },
      { id: 'models', label: 'Model Comparison', iconName: 'Cpu', badge: 'v1.0-v2.1' },
      { id: 'reports', label: 'Trial Reports', iconName: 'FileText' },
      { id: 'users', label: 'Research Team', iconName: 'Users' },
    ],
  },
  'Data Scientist': {
    roleTitle: 'Data Scientist',
    badgeColor: 'bg-blue-50 text-blue-700 border-blue-200',
    homeScreen: 'dashboard',
    allowedScreens: ['dashboard', 'upload', 'config', 'models', 'results', 'cases', 'case-detail'],
    navItems: [
      { id: 'dashboard', label: 'Model Dashboard', iconName: 'Cpu', badge: 'RTX 2050' },
      { id: 'upload', label: 'Scan Ingestion', iconName: 'UploadCloud', badge: '512x512' },
      { id: 'config', label: 'Model Tuning', iconName: 'Sliders' },
      { id: 'models', label: 'Model Comparison', iconName: 'BarChart3', badge: 'v1.0-v2.1' },
      { id: 'results', label: 'Validation Metrics', iconName: 'Activity' },
      { id: 'cases', label: 'Benchmark Cases', iconName: 'FolderKanban' },
    ],
  },
  'Administrator': {
    roleTitle: 'Administrator',
    badgeColor: 'bg-slate-100 text-slate-700 border-slate-300',
    homeScreen: 'dashboard',
    allowedScreens: ['dashboard', 'users', 'cases', 'reports', 'models'],
    navItems: [
      { id: 'dashboard', label: 'System Telemetry', iconName: 'Activity' },
      { id: 'users', label: 'User & Access', iconName: 'Users' },
      { id: 'cases', label: 'File Audits', iconName: 'FolderKanban' },
      { id: 'models', label: 'Model Comparison', iconName: 'Cpu', badge: 'v1.0-v2.1' },
      { id: 'reports', label: 'Server Logs', iconName: 'Terminal' },
    ],
  },
};

// Granular RBAC Permission Helpers
export type ModelConfigMode = 'full-tuning' | 'best-model-locked' | 'restricted';
export type CaseAccessMode = 'full' | 'clinical' | 'research-deidentified' | 'benchmark-only' | 'audit-only';

export const canUploadScans = (role?: UserRole): boolean =>
  Boolean(role && ['Developer', 'Radiologist / Clinician', 'Medical Researcher', 'Data Scientist'].includes(role));

export const getModelConfigMode = (role?: UserRole): ModelConfigMode => {
  if (!role) return 'restricted';
  if (['Developer', 'Data Scientist'].includes(role)) return 'full-tuning';
  if (['Radiologist / Clinician', 'Medical Researcher'].includes(role)) return 'best-model-locked';
  return 'restricted';
};

export const canSignReports = (role?: UserRole): boolean => role === 'Radiologist / Clinician';

export const canGenerateReports = (role?: UserRole): boolean =>
  Boolean(role && ['Radiologist / Clinician', 'Developer'].includes(role));

export const canManageUsers = (role?: UserRole): boolean =>
  Boolean(role && ['Administrator', 'Developer'].includes(role));

export const canDeployModels = (role?: UserRole): boolean =>
  Boolean(role && ['Developer', 'Data Scientist'].includes(role));

export const getCaseAccessMode = (role?: UserRole): CaseAccessMode => {
  switch (role) {
    case 'Developer': return 'full';
    case 'Radiologist / Clinician': return 'clinical';
    case 'Medical Researcher': return 'research-deidentified';
    case 'Data Scientist': return 'benchmark-only';
    case 'Administrator': return 'audit-only';
    default: return 'clinical';
  }
};

export const getAllowedExports = (role?: UserRole): ('pdf' | 'json' | 'csv')[] => {
  switch (role) {
    case 'Developer': return ['pdf', 'json', 'csv'];
    case 'Radiologist / Clinician': return ['pdf', 'json'];
    case 'Medical Researcher': return ['csv', 'json'];
    case 'Data Scientist': return ['json', 'csv'];
    case 'Administrator': return ['csv'];
    default: return ['json'];
  }
};
