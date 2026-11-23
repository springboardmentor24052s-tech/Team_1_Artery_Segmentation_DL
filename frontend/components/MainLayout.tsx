'use client';

import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { SystemUser } from '@/lib/mockData';

interface MainLayoutProps {
  currentScreen: string;
  onNavigate: (screen: string) => void;
  onLogout: () => void;
  currentUser: SystemUser;
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  currentScreen,
  onNavigate,
  onLogout,
  currentUser,
  children,
}) => {
  const getScreenTitle = () => {
    switch (currentScreen) {
      case 'dashboard':
        if (currentUser.role === 'Developer') return 'Artery Segmentation and Stenosis Detection';
        if (currentUser.role === 'Medical Researcher') return 'Clinical Research Dashboard & Cohort Telemetry';
        if (currentUser.role === 'Radiologist / Clinician') return 'Diagnostic Reading Worklist & Clinical Decision Support';
        if (currentUser.role === 'Data Scientist') return 'Model Performance Engineering & Benchmark Telemetry';
        if (currentUser.role === 'Administrator') return 'System Infrastructure, GPU Health & RBAC Telemetry';
        return 'Overview & Telemetry';
      case 'cases':
        if (currentUser.role === 'Developer') return 'Case Management';
        if (currentUser.role === 'Radiologist / Clinician') return 'Patient Clinical Angiogram Worklist';
        if (currentUser.role === 'Medical Researcher') return 'Cohort Studies & Angiogram Repository';
        return 'Coronary Case Repository (ARCADE Benchmark)';
      case 'upload':
        if (currentUser.role === 'Developer') return 'Image Upload & Processing';
        return 'Coronary Angiogram Ingestion & Preprocessing';
      case 'config':
        if (currentUser.role === 'Developer') return 'Model Configuration';
        return 'Model Hyperparameters & QCA Thresholds';
      case 'models':
        return 'Model Comparison';
      case 'results':
        if (currentUser.role === 'Developer') return 'Analysis Results';
        return 'Diagnostic Findings: QCA Calipers & Grad-CAM XAI Saliency';
      case 'case-detail':
        return 'Detailed Case Examination & Multi-Panel Viewer';
      case 'reports':
        if (currentUser.role === 'Developer') return 'Reports & Activity';
        if (currentUser.role === 'Radiologist / Clinician') return 'Clinical Patient Sign-Off Reports';
        if (currentUser.role === 'Administrator') return 'System & Server Diagnostic Audit Logs';
        return 'Clinical Research Reports & Publications';
      case 'users':
        if (currentUser.role === 'Developer') return 'User Management';
        return 'Platform Identity & Access Management (RBAC)';
      default:
        return 'StenoVision PACS Workstation';
    }
  };

  return (
    <div className="flex h-screen bg-[#1c1c1c] text-[#252525] font-sans antialiased overflow-hidden">
      {/* Dark Clinical PACS Sidebar with Brand Crimson Linings */}
      <Sidebar
        currentScreen={currentScreen}
        onNavigate={onNavigate}
        onLogout={onLogout}
        currentUser={currentUser}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-[#FAF9F9]">
        <Header
          currentScreenTitle={getScreenTitle()}
          currentUser={currentUser}
          onLogout={onLogout}
        />

        <main className="flex-1 overflow-y-auto p-8 relative">
          <div className="max-w-7xl mx-auto space-y-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
