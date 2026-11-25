'use client';

import React, { useState, useRef, useEffect } from 'react';
import Image from 'next/image';
import { ChevronDown, Shield, Stethoscope, Cpu, ShieldCheck, Terminal, LogOut, Lock, Menu, User as UserIcon } from 'lucide-react';
import { SystemUser } from '@/lib/mockData';
import { UserRole } from '@/lib/permissions';
import { UserAvatar } from './UserAvatar';

interface HeaderProps {
  currentScreenTitle: string;
  currentUser: SystemUser;
  onLogout?: () => void;
  onOpenMobileMenu?: () => void;
  headerBadge?: React.ReactNode;
  headerActions?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({
  currentScreenTitle,
  currentUser,
  onLogout,
  onOpenMobileMenu,
  headerBadge,
  headerActions,
}) => {
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

  // Close profile dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getRoleIcon = (role: UserRole) => {
    switch (role) {
      case 'Developer':
        return <Terminal className="w-3.5 h-3.5 text-amber-600" />;
      case 'Radiologist / Clinician':
        return <Stethoscope className="w-3.5 h-3.5 text-red-600" />;
      case 'Medical Researcher':
        return <Shield className="w-3.5 h-3.5 text-purple-600" />;
      case 'Data Scientist':
        return <Cpu className="w-3.5 h-3.5 text-blue-600" />;
      case 'Administrator':
        return <ShieldCheck className="w-3.5 h-3.5 text-slate-700" />;
      default:
        return <Shield className="w-3.5 h-3.5 text-slate-600" />;
    }
  };

  const getRoleBadgeStyle = (role: UserRole) => {
    switch (role) {
      case 'Developer':
        return 'bg-amber-50 text-amber-800 border-amber-300';
      case 'Radiologist / Clinician':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'Medical Researcher':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'Data Scientist':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'Administrator':
        return 'bg-slate-100 text-slate-700 border-slate-300';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <header className="h-16 bg-white border-b border-[#A91121]/20 px-4 sm:px-8 flex items-center justify-between gap-2 shrink-0 shadow-sm relative z-30">
      {/* Title Zone with Mobile Menu Trigger & Standalone Emblem */}
      <div className="flex items-center gap-3 sm:gap-4 min-w-0 flex-1">
        {onOpenMobileMenu && (
          <button
            type="button"
            onClick={onOpenMobileMenu}
            className="md:hidden p-2 -ml-1 rounded-lg text-slate-600 hover:text-[#A91121] hover:bg-red-50 border border-slate-200 transition-colors shrink-0"
            aria-label="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <div className="relative hidden sm:flex w-10 h-10 rounded-xl bg-white border border-[#A91121]/20 items-center justify-center p-0.5 shadow-sm shrink-0 overflow-hidden">
          <Image
            src="/assets/aistudio/image_39582843.png"
            alt="StenoVision Emblem"
            fill
            className="object-contain p-0.5"
            referrerPolicy="no-referrer"
          />
        </div>
        <div className="flex items-center gap-2.5 min-w-0">
          <h1 className="text-sm sm:text-base font-bold text-[#252525] tracking-tight truncate">{currentScreenTitle}</h1>
          {headerBadge}
        </div>
      </div>

      {/* Right Controls & Role-Locked Authenticated Profile */}
      <div className="flex items-center gap-3">
        {headerActions}

        {/* Authenticated User Menu (Role Locked - Direct Switching Disabled) */}
        <div className="relative" ref={profileRef}>
          <button
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-2.5 px-3 py-1.5 bg-[#F9F9F9] hover:bg-[#F2F2F2] border border-[#A91121]/20 hover:border-[#A91121]/40 rounded-xl transition-all shadow-sm group"
            title="Authenticated Clinical Profile & Session"
          >
            <UserAvatar role={currentUser.role} size="md" />
            <div className="hidden sm:flex items-center gap-2 text-left">
              <span className="text-xs font-bold text-[#252525]">{currentUser.name}</span>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-medium ${getRoleBadgeStyle(currentUser.role)}`}>
                {currentUser.role}
              </span>
            </div>
            <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${profileOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Profile & Sign Out Popover */}
          {profileOpen && (
            <div className="absolute right-0 mt-2 w-72 bg-white border border-[#A91121]/20 rounded-2xl shadow-xl p-4 z-50 animate-in fade-in slide-in-from-top-2 duration-150 space-y-3">
              {/* User Identity Details */}
              <div className="flex items-start gap-3 pb-3 border-b border-slate-100">
                <UserAvatar role={currentUser.role} size="lg" />
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-bold text-[#252525] truncate">{currentUser.name}</div>
                  <div className="text-[11px] text-slate-500 font-mono truncate">{currentUser.email}</div>
                  <div className="mt-1 flex items-center gap-1.5">
                    <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded border font-medium ${getRoleBadgeStyle(currentUser.role)}`}>
                      {currentUser.role}
                    </span>
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0"></span>
                  </div>
                </div>
              </div>

              {/* Security / Role Notice */}
              <div className="p-2.5 bg-slate-50 rounded-xl border border-slate-200 text-[11px] text-slate-600 flex items-start gap-2">
                <Lock className="w-3.5 h-3.5 text-[#A91121] shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-slate-800">Session Locked</span>: To protect patient data integrity and audit trails, role-switching is locked. Sign out to change profiles.
                </div>
              </div>

              {/* Sign Out Button */}
              {onLogout && (
                <button
                  onClick={() => {
                    setProfileOpen(false);
                    onLogout();
                  }}
                  className="w-full flex items-center justify-center gap-2 py-2 px-3 bg-red-50 hover:bg-red-100 text-red-700 hover:text-red-800 font-semibold text-xs rounded-xl border border-red-200 transition-colors shadow-sm"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out of Session</span>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Quick Sign Out Action in Header */}
        {onLogout && (
          <button
            onClick={onLogout}
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-red-700 hover:bg-red-50 border border-slate-200 hover:border-red-200 rounded-xl transition-all shadow-sm"
            title="Sign out of current clinical session"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        )}
      </div>
    </header>
  );
};
