import React from 'react';
import { LucideIcon } from 'lucide-react';

interface SummaryCardProps {
  title: string;
  value: string | number;
  change?: string;
  isPositive?: boolean;
  icon: LucideIcon;
  description?: string;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  value,
  change,
  isPositive = true,
  icon: Icon,
  description
}) => {
  return (
    <div className="bg-white border border-[#A91121]/20 rounded-xl p-5 shadow-sm hover:border-[#A91121]/40 transition-all flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</span>
        <div className="w-8 h-8 bg-transparent text-[#A91121] flex items-center justify-center">
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="my-3">
        <div className="text-2xl font-bold font-mono text-[#252525] tracking-tight">{value}</div>
        {change && (
          <div className="flex items-center gap-1.5 mt-1">
            <span className={`text-xs font-semibold font-mono ${isPositive ? 'text-emerald-600' : 'text-[#A91121]'}`}>
              {change}
            </span>
            {description && <span className="text-xs text-slate-400">· {description}</span>}
          </div>
        )}
        {!change && description && (
          <p className="text-xs text-slate-500 mt-1">{description}</p>
        )}
      </div>
    </div>
  );
};
