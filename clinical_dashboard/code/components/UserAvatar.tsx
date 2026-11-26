'use client';

import React from 'react';
import { UserRole } from '@/lib/permissions';
import { Terminal, Stethoscope, Microscope, Cpu, ShieldCheck, User } from 'lucide-react';

interface UserAvatarProps {
  role?: UserRole | string;
  isDark?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const UserAvatar: React.FC<UserAvatarProps> = ({
  role = 'Developer',
  isDark = false,
  size = 'md',
  className = '',
}) => {
  const getTheme = () => {
    switch (role) {
      case 'Developer':
        return {
          icon: Terminal,
          light: 'bg-amber-50 text-amber-800 border-amber-300',
          dark: 'bg-amber-950/60 text-[#F6A16B] border-amber-500/40',
        };
      case 'Radiologist / Clinician':
        return {
          icon: Stethoscope,
          light: 'bg-red-50 text-[#A91121] border-red-200',
          dark: 'bg-red-950/60 text-red-400 border-red-500/40',
        };
      case 'Medical Researcher':
        return {
          icon: Microscope,
          light: 'bg-purple-50 text-purple-700 border-purple-200',
          dark: 'bg-purple-950/60 text-purple-400 border-purple-500/40',
        };
      case 'Data Scientist':
        return {
          icon: Cpu,
          light: 'bg-blue-50 text-blue-700 border-blue-200',
          dark: 'bg-blue-950/60 text-blue-400 border-blue-500/40',
        };
      case 'Administrator':
        return {
          icon: ShieldCheck,
          light: 'bg-slate-100 text-slate-800 border-slate-300',
          dark: 'bg-slate-800 text-slate-300 border-slate-600',
        };
      default:
        return {
          icon: User,
          light: 'bg-slate-100 text-slate-700 border-slate-300',
          dark: 'bg-[#333333] text-slate-300 border-[#444444]',
        };
    }
  };

  const theme = getTheme();
  const IconComponent = theme.icon;

  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
  }[size];

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  }[size];

  return (
    <div
      className={`rounded-full flex items-center justify-center shrink-0 border shadow-2xs transition-all ${sizeClasses} ${
        isDark ? theme.dark : theme.light
      } ${className}`}
    >
      <IconComponent className={iconSizes} />
    </div>
  );
};

