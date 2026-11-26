import React from 'react';
import { Filter } from 'lucide-react';

interface FilterOption {
  label: string;
  value: string;
}

interface FilterControlsProps {
  label: string;
  options: FilterOption[];
  selectedValue: string;
  onChange: (value: string) => void;
  className?: string;
}

export const FilterControls: React.FC<FilterControlsProps> = ({
  label,
  options,
  selectedValue,
  onChange,
  className = ''
}) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="text-xs font-medium text-slate-500 whitespace-nowrap flex items-center gap-1">
        <Filter className="w-3 h-3 text-[#A91121]" />
        {label}:
      </span>
      <div className="flex items-center bg-[#F5F5F5] p-0.5 rounded-lg border border-[#A91121]/20">
        {options.map((opt) => {
          const isActive = selectedValue === opt.value;
          return (
            <button
              key={opt.value}
              onClick={() => onChange(opt.value)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-all whitespace-nowrap ${
                isActive
                  ? 'bg-[#A91121] text-white shadow-sm'
                  : 'text-slate-600 hover:text-[#252525]'
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};
