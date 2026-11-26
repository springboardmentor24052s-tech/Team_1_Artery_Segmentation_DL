'use client';

import React from 'react';
import Image from 'next/image';
import {
  LayoutDashboard,
  FolderKanban,
  UploadCloud,
  Sliders,
  BarChart3,
  FileText,
  Users,
  Cpu,
  Activity,
  ShieldAlert,
  Microscope,
  Terminal,
  FileCheck,
  LogOut,
  Shield,
  Monitor,
  Folder,
  User,
  X
} from 'lucide-react';
import { SystemUser } from '@/lib/mockData';
import { ROLE_CONFIGURATIONS, NavItemDef } from '@/lib/permissions';
import { UserAvatar } from './UserAvatar';

interface SidebarProps {
  currentScreen: string;
  onNavigate: (screen: string) => void;
  onLogout: () => void;
  currentUser: SystemUser;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

const ICON_MAP = {
  LayoutDashboard,
  FolderKanban,
  Folder,
  UploadCloud,
  Sliders,
  BarChart3,
  FileText,
  Users,
  Cpu,
  Activity,
  ShieldAlert,
  Microscope,
  Terminal,
  FileCheck,
  Monitor,
};

export const Sidebar: React.FC<SidebarProps> = ({
  currentScreen,
  onNavigate,
  onLogout,
  currentUser,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  const roleConfig = ROLE_CONFIGURATIONS[currentUser.role] || ROLE_CONFIGURATIONS['Radiologist / Clinician'];
  const navItems = roleConfig.navItems;

  const handleNavClick = (screenId: string) => {
    onNavigate(screenId);
    onCloseMobile?.();
  };

  const sidebarContent = (
    <>
      {/* Brand Header with Standalone Emblem */}
      <div className="h-20 flex items-center px-4 gap-3 border-b border-[#333333] bg-[#1e1e1e]">
        <div className="relative w-12 h-12 rounded-xl overflow-hidden bg-white flex items-center justify-center p-0.5 shrink-0 shadow-md">
          <Image
            src="/assets/aistudio/image_39582843.png"
            alt="StenoVision Emblem"
            fill
            className="object-contain p-0.5"
            referrerPolicy="no-referrer"
          />
        </div>
        <div className="overflow-hidden flex-1 min-w-0">
          <div className="text-sm font-bold text-white tracking-tight truncate">StenoVision</div>
          <div className="text-[10px] font-mono text-slate-400 uppercase tracking-widest truncate font-medium">
            Coronary AI Platform
          </div>
        </div>
        {onCloseMobile && (
          <button
            type="button"
            onClick={onCloseMobile}
            className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#333333] transition-colors"
            aria-label="Close navigation menu"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Navigation List - Role Specific */}
      <nav className="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 flex items-center justify-between text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
          <span>Navigation</span>
          <span className="font-mono text-[#F6A16B] truncate max-w-[120px]">{currentUser.role}</span>
        </div>

        {navItems.map((item) => {
          const Icon = ICON_MAP[item.iconName] || LayoutDashboard;
          const isActive =
            currentScreen === item.id ||
            (currentScreen === 'case-detail' && item.id === 'cases');

          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-[#A91121]/20 text-[#ff6b7a] font-bold border border-[#A91121]/40 shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-[#333333]/60'
              }`}
            >
              <div className="flex items-center gap-3 truncate">
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-[#ff6b7a]' : 'text-slate-400'}`} />
                <span className="truncate">{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#333333] text-slate-300 border border-[#444444] shrink-0">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Active Persona Footer Badge: Name & Role strictly */}
      <div className="p-3 bg-[#1a1a1a] border-t border-[#333333] space-y-2">
        <div className="flex items-center gap-2.5 px-2.5 py-2 bg-[#252525] rounded-lg border border-[#333333]">
          <UserAvatar role={currentUser.role} isDark={true} size="md" />
          <div className="min-w-0 flex-1">
            <div className="text-xs font-bold text-white truncate flex items-center gap-1.5">
              <span>{currentUser.name}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shrink-0"></span>
            </div>
            <div className="text-[11px] font-mono text-[#F6A16B] truncate font-medium">{currentUser.role}</div>
          </div>
        </div>

        <button
          onClick={() => {
            onCloseMobile?.();
            onLogout();
          }}
          className="w-full flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-red-400 hover:bg-red-950/30 rounded-lg border border-[#333333] transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </>
  );

  return (
    <>
      <aside className="hidden md:flex w-64 bg-[#252525] text-slate-300 flex-col shrink-0 border-r border-[#333333] select-none">
        {sidebarContent}
      </aside>

      {isMobileOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-xs"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
          <aside className="relative z-10 w-72 max-w-[85vw] bg-[#252525] text-slate-300 flex flex-col border-r border-[#333333] select-none shadow-2xl">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
};
