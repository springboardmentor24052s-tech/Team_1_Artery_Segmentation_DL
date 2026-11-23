'use client';

import React, { useState, useEffect } from 'react';
import { MainLayout } from '@/components/MainLayout';
import { LoginScreen } from '@/components/screens/LoginScreen';
import { DashboardScreen } from '@/components/screens/DashboardScreen';
import { CaseManagementScreen } from '@/components/screens/CaseManagementScreen';
import { UploadMedicalImageScreen } from '@/components/screens/UploadMedicalImageScreen';
import { AnalysisConfigScreen } from '@/components/screens/AnalysisConfigScreen';
import { AnalysisResultsScreen } from '@/components/screens/AnalysisResultsScreen';
import { CaseDetailsScreen } from '@/components/screens/CaseDetailsScreen';
import { ReportsScreen } from '@/components/screens/ReportsScreen';
import { UserManagementScreen } from '@/components/screens/UserManagementScreen';
import { ModelComparisonView } from '@/components/ModelComparisonView';
import { DiagnosticResult, UploadedScanPayload } from '@/lib/api';
import { INITIAL_USERS, SystemUser } from '@/lib/mockData';
import { ROLE_CONFIGURATIONS } from '@/lib/permissions';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export default function Page() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [currentUser, setCurrentUser] = useState<SystemUser>(
    INITIAL_USERS.find(u => u.role === 'Radiologist / Clinician') || INITIAL_USERS[0]
  );
  const [currentScreen, setCurrentScreen] = useState<string>('dashboard');
  const [selectedCaseId, setSelectedCaseId] = useState<string>('CASE-1010');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadedPayload, setUploadedPayload] = useState<UploadedScanPayload | null>(null);
  const [latestAnalysisResult, setLatestAnalysisResult] = useState<DiagnosticResult | null>(null);

  // Restore authenticated session from localStorage if available
  useEffect(() => {
    try {
      const savedUserJson = localStorage.getItem('stenovision_active_user');
      if (savedUserJson) {
        const savedUser = JSON.parse(savedUserJson);
        if (savedUser && savedUser.id) {
          setCurrentUser(savedUser);
          setIsAuthenticated(true);
        }
      }
    } catch {
      // Ignore storage read error
    }
  }, []);

  const handleNavigate = (screen: string, caseId?: string) => {
    if (caseId) {
      setSelectedCaseId(caseId);
    }
    setCurrentScreen(screen);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLogin = (user: SystemUser, token?: string) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
    const roleConfig = ROLE_CONFIGURATIONS[user.role];
    setCurrentScreen(roleConfig ? roleConfig.homeScreen : 'dashboard');
    try {
      localStorage.setItem('stenovision_active_user', JSON.stringify(user));
      if (token) {
        localStorage.setItem('stenovision_token', token);
      }
    } catch {
      // Ignore storage write error
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    try {
      localStorage.removeItem('stenovision_active_user');
      localStorage.removeItem('stenovision_token');
    } catch {
      // Ignore storage removal error
    }
    setCurrentScreen('dashboard');
  };

  if (!isAuthenticated) {
    return (
      <LoginScreen
        onLogin={handleLogin}
        allUsers={INITIAL_USERS}
      />
    );
  }

  // Check RBAC permissions for the requested screen
  const roleConfig = ROLE_CONFIGURATIONS[currentUser.role] || ROLE_CONFIGURATIONS['Radiologist / Clinician'];
  const isAllowed = roleConfig.allowedScreens.includes(currentScreen);

  return (
    <MainLayout
      currentScreen={currentScreen}
      onNavigate={handleNavigate}
      onLogout={handleLogout}
      currentUser={currentUser}
    >
      {!isAllowed ? (
        <div className="bg-white border border-[#A91121]/20 rounded-xl p-12 text-center max-w-lg mx-auto space-y-4 shadow-sm my-12">
          <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-full flex items-center justify-center mx-auto border border-amber-200">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-[#252525]">Role-Restricted Workflow</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            The screen <code className="font-mono text-[#A91121] bg-red-50 px-1 py-0.5 rounded">{currentScreen}</code> is restricted for your active role (<strong className="text-slate-800">{currentUser.role}</strong>) to guarantee separation of concerns and prevent feature collision.
          </p>
          <button
            onClick={() => setCurrentScreen(roleConfig.homeScreen)}
            className="px-4 py-2 bg-[#A91121] text-white text-xs font-semibold rounded-lg shadow-sm hover:bg-[#800D1B] inline-flex items-center gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Return to My Dashboard
          </button>
        </div>
      ) : (
        <>
          {currentScreen === 'dashboard' && (
            <DashboardScreen currentUser={currentUser} onNavigate={handleNavigate} />
          )}
          {currentScreen === 'cases' && (
            <CaseManagementScreen currentUser={currentUser} onNavigate={handleNavigate} />
          )}
          {currentScreen === 'upload' && (
            <UploadMedicalImageScreen
              currentUser={currentUser}
              onNavigate={handleNavigate}
              onFileIngested={(file, payload) => {
                setUploadedFile(file);
                if (payload) setUploadedPayload(payload);
              }}
            />
          )}
          {currentScreen === 'config' && (
            <AnalysisConfigScreen
              currentUser={currentUser}
              onNavigate={handleNavigate}
              uploadedFile={uploadedFile}
              uploadedPayload={uploadedPayload}
              onAnalysisComplete={(result) => {
                setLatestAnalysisResult(result);
                handleNavigate('results');
              }}
            />
          )}
          {currentScreen === 'models' && (
            <ModelComparisonView currentUser={currentUser} />
          )}
          {currentScreen === 'results' && (
            <AnalysisResultsScreen
              currentUser={currentUser}
              onNavigate={handleNavigate}
              analysisResult={latestAnalysisResult}
            />
          )}
          {currentScreen === 'case-detail' && (
            <CaseDetailsScreen
              caseId={selectedCaseId}
              currentUser={currentUser}
              onNavigate={handleNavigate}
            />
          )}
          {currentScreen === 'reports' && (
            <ReportsScreen currentUser={currentUser} onNavigate={handleNavigate} />
          )}
          {currentScreen === 'users' && (
            <UserManagementScreen currentUser={currentUser} onNavigate={handleNavigate} />
          )}
        </>
      )}
    </MainLayout>
  );
}
