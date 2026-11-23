import React from 'react';
import { CheckCircle2, Clock, AlertTriangle, XCircle } from 'lucide-react';

interface StatusIndicatorProps {
  status:
  | 'Completed'
  | 'Processing'
  | 'Pending Review'
  | 'Failed'
  | 'Active'
  | 'Inactive'
  | 'Normal'
  | 'Mild'
  | 'Moderate'
  | 'Severe'
  | 'Critical';
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, className = '' }) => {
  let icon = <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />;
  let badgeStyle = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  let label = status;

  switch (status) {
    case 'Completed':
    case 'Active':
    case 'Normal':
      icon = <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />;
      badgeStyle = 'bg-emerald-50 text-emerald-700 border-emerald-200';
      break;
    case 'Mild':
      icon = <CheckCircle2 className="w-3.5 h-3.5 text-blue-600 shrink-0" />;
      badgeStyle = 'bg-blue-50 text-blue-700 border-blue-200';
      break;
    case 'Moderate':
    case 'Processing':
    case 'Pending Review':
      icon = <Clock className="w-3.5 h-3.5 text-amber-600 shrink-0" />;
      badgeStyle = 'bg-amber-50 text-amber-700 border-amber-200';
      break;
    case 'Severe':
      icon = <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />;
      badgeStyle = 'bg-rose-50 text-rose-700 border-rose-200';
      break;
    case 'Critical':
      icon = <AlertTriangle className="w-3.5 h-3.5 text-white shrink-0" />;
      badgeStyle = 'bg-red-900 text-white border-red-950 font-bold';
      break;
    case 'Failed':
    case 'Inactive':
      icon = <XCircle className="w-3.5 h-3.5 text-slate-500 shrink-0" />;
      badgeStyle = 'bg-slate-100 text-slate-600 border-slate-200';
      break;
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-medium rounded border ${badgeStyle} ${className}`}>
      {icon}
      <span>{label}</span>
    </span>
  );
};
