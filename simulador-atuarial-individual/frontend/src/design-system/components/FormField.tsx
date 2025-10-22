import React from 'react';
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

  const LabelContent = (
    <label
      htmlFor={htmlFor}
      className={`${labelClass} ${tooltip ? 'cursor-help' : ''}`}
    >
      {label}
      {required && <span className="text-red-500 ml-1">*</span>}
    </label>
  );

  return (
    <div className={containerClass}>
      {tooltip ? (
        <Tooltip content={tooltip}>
          {LabelContent}
        </Tooltip>
      ) : (
        LabelContent
      )}
      {children}
      {helper && (
        <p className="text-xs text-slate-500 leading-tight mt-1">
          {helper}
        </p>
      )}
    </div>
  );
};