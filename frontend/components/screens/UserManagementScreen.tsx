'use client';

import React, { useState } from 'react';
import { INITIAL_USERS, SystemUser } from '@/lib/mockData';
import { UserRole, canManageUsers } from '@/lib/permissions';
import { DataTable, Column } from '../DataTable';
import { StatusIndicator } from '../StatusIndicator';
import { UserAvatar } from '../UserAvatar';
import { Users, UserPlus, Check, ArrowRight, X, ShieldCheck } from 'lucide-react';

interface UserManagementScreenProps {
  onNavigate: (screen: string) => void;
  currentUser?: SystemUser;
  onSwitchUser?: (user: SystemUser) => void;
}

export const UserManagementScreen: React.FC<UserManagementScreenProps> = ({
  currentUser,
  onSwitchUser,
}) => {
  const [users, setUsers] = useState<SystemUser[]>(INITIAL_USERS);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState<UserRole>('Data Scientist');

  const handleAddUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName || !newEmail) return;
    const user: SystemUser = {
      id: 'USR-' + (users.length + 10),
      name: newName,
      email: newEmail,
      role: newRole,
      status: 'Active',
      lastActive: 'Just now'
    };
    setUsers([user, ...users]);
    setNewName('');
    setNewEmail('');
    setShowAddModal(false);
  };

  const getRoleBadgeStyle = (role: string) => {
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

  const columns: Column<SystemUser>[] = [
    {
      header: 'USER NAME & EMAIL',
      accessorKey: (row) => (
        <div className="flex items-center gap-3">
          <UserAvatar role={row.role} size="md" />
          <div className="min-w-0">
            <div className="font-semibold text-[#252525] flex items-center gap-1.5">
              <span>{row.name}</span>
              {currentUser && currentUser.id === row.id && (
                <span className="text-[10px] font-mono font-bold bg-[#A91121] text-white px-1.5 py-0.2 rounded">
                  YOU
                </span>
              )}
            </div>
            <div className="text-xs font-mono text-slate-500">{row.email}</div>
          </div>
        </div>
      ),
    },
    {
      header: 'ROLE',
      accessorKey: (row) => (
        <span className={`font-mono text-xs font-medium px-2 py-0.5 rounded border ${getRoleBadgeStyle(row.role)}`}>
          {row.role}
        </span>
      ),
    },
    { header: 'STATUS', accessorKey: (row) => <StatusIndicator status={row.status} /> },
    { header: 'LAST ACTIVE', accessorKey: 'lastActive', className: 'text-xs text-slate-500 font-mono' },
    {
      header: 'PERSONA ACTION',
      accessorKey: (row) => {
        const isCurrent = currentUser && currentUser.id === row.id;
        const isResearcher = currentUser?.role === 'Medical Researcher';

        if (isResearcher) {
          return (
            <div className="text-right">
              {isCurrent ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold text-emerald-700 bg-emerald-50 rounded border border-emerald-200">
                  <Check className="w-3.5 h-3.5" /> Active Persona
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-500 bg-slate-50 rounded border border-slate-200">
                  Research Peer
                </span>
              )}
            </div>
          );
        }

        return (
          <div className="text-right">
            {isCurrent ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold text-emerald-700 bg-emerald-50 rounded border border-emerald-200">
                <Check className="w-3.5 h-3.5" /> Active Persona
              </span>
            ) : (
              <button
                onClick={() => onSwitchUser && onSwitchUser(row)}
                className="px-2.5 py-1 text-xs font-semibold text-[#A91121] bg-[#A91121]/10 hover:bg-[#A91121]/20 rounded-md transition-colors inline-flex items-center gap-1 shadow-sm cursor-pointer"
              >
                Switch to Role <ArrowRight className="w-3 h-3" />
              </button>
            )}
          </div>
        );
      },
      className: 'text-right',
    },
  ];

  const isResearcher = currentUser?.role === 'Medical Researcher';

  return (
    <div className="space-y-6">
      {/* Top Action Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-[#252525]">
            {isResearcher ? 'Research Personnel Directory' : 'User & Access Management'}
          </h2>
          <p className="text-xs text-slate-500">
            {isResearcher
              ? 'View authorized research collaborators, clinical investigators, and lab staff'
              : 'Manage investigator privileges, radiology credentials, and lab security access controls'}
          </p>
        </div>
        {canManageUsers(currentUser?.role) && (
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 text-xs font-semibold text-white bg-[#A91121] hover:bg-[#800D1B] rounded-lg transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
          >
            <UserPlus className="w-4 h-4" /> Add User
          </button>
        )}
      </div>

      {/* Add User Modal with Proper Fixed Backdrop */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-2xl w-full max-w-md space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-red-50 text-[#A91121]">
                  <UserPlus className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#252525]">Provision New User</h3>
                  <p className="text-xs text-slate-500">Assign Role-Based Access Control (RBAC) privileges</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
                title="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddUser} className="space-y-3.5 text-xs">
              <div className="space-y-1">
                <label className="block font-semibold text-[#252525]">Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. Dr. John Doe"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#A91121]/20 focus:border-[#A91121] transition-all"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="block font-semibold text-[#252525]">Email Address</label>
                <input
                  type="email"
                  placeholder="e.g. j.doe@stenovision.org"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#A91121]/20 focus:border-[#A91121] transition-all"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="block font-semibold text-[#252525]">Assigned RBAC Role</label>
                <select
                  value={newRole}
                  onChange={(e) => setNewRole(e.target.value as any)}
                  className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#A91121]/20 focus:border-[#A91121] transition-all cursor-pointer"
                >
                  <option value="Developer">Developer (Unrestricted Platform Superuser)</option>
                  <option value="Radiologist / Clinician">Radiologist / Clinician (Diagnostic &amp; Sign-Off Worklist)</option>
                  <option value="Medical Researcher">Medical Researcher (Cohort Studies &amp; QCA Repository)</option>
                  <option value="Data Scientist">Data Scientist (Model Engineering &amp; Benchmarks)</option>
                  <option value="Administrator">Administrator (Audit Logs &amp; Infrastructure)</option>
                </select>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-slate-600 leading-relaxed">
                <strong className="text-[#252525] block mb-0.5">Role Permission Scope:</strong>
                {newRole === 'Developer' && 'Full platform telemetry, model fine-tuning, system configuration, and user provisioning.'}
                {newRole === 'Radiologist / Clinician' && 'Direct clinical case review, QCA caliper verification, and legal electronic sign-off.'}
                {newRole === 'Medical Researcher' && 'Cohort study querying, multi-case quantitative QCA analysis, and CSV/PDF export.'}
                {newRole === 'Data Scientist' && 'Neural network latency benchmarks, radar trade-off evaluation, and model comparison.'}
                {newRole === 'Administrator' && 'HIPAA compliance audit logs, GPU cluster telemetry, and account management.'}
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-bold rounded-lg bg-[#A91121] text-white hover:bg-[#8B0E1B] transition-colors shadow-sm cursor-pointer"
                >
                  Provision User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* User Directory Table: Name & Role strictly */}
      <DataTable
        data={users}
        columns={columns}
        keyExtractor={(row) => row.id}
      />
    </div>
  );
};
