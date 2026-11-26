import React from 'react';

interface FormInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  helperText?: string;
}

export const FormInput: React.FC<FormInputProps> = ({
  label,
  error,
  helperText,
  id,
  className = '',
  ...props
}) => {
  const inputId = id || label.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className={`space-y-1.5 ${className}`}>
      <label htmlFor={inputId} className="block text-xs font-semibold text-[#252525]">
        {label} {props.required && <span className="text-[#A91121]">*</span>}
      </label>
      <input
        id={inputId}
        className={`w-full px-3.5 py-2 text-sm bg-white border rounded-lg text-[#252525] placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#A91121]/25 transition-all font-sans ${
          error ? 'border-rose-500 focus:border-rose-500' : 'border-[#A91121]/20 focus:border-[#A91121]'
        }`}
        {...props}
      />
      {error && <p className="text-xs text-rose-600 font-medium">{error}</p>}
      {helperText && !error && <p className="text-xs text-slate-500">{helperText}</p>}
    </div>
  );
};
