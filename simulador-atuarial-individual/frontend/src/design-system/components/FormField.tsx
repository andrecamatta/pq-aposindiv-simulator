import React from 'react';
import { HelpCircle } from 'lucide-react';
import { Tooltip } from './Tooltip';

interface FormFieldProps {
  label: string;
  tooltip?: string;
  helper?: string;
  required?: boolean;
  children: React.ReactNode;
  className?: string;
  htmlFor?: string;
  /** Se deve usar o estilo compacto (padrão) ou expandido (ParticipantSection) */
  variant?: 'default' | 'expanded';
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  tooltip,
  helper,
  required = false,
  children,
  className,
  htmlFor,
  variant = 'default'
}) => {
  const containerClass = variant === 'expanded'
    ? "space-y-2"
    : className || "space-y-1.5";

  const labelClass = variant === 'expanded'
    ? "block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1"
    : "text-sm font-medium text-gray-700";

  return (
    <div className={containerClass}>
      <div className="flex items-center gap-2">
        <label
          htmlFor={htmlFor}
          className={labelClass}
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        {tooltip && (
          <Tooltip content={tooltip}>
            <HelpCircle className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" />
          </Tooltip>
        )}
      </div>
      {children}
      {helper && (
        <p className="text-xs text-slate-500 leading-tight mt-1">
          {helper}
        </p>
      )}
    </div>
  );
};