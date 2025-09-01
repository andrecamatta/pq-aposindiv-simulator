import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';
import { ChevronDown } from 'lucide-react';

const selectVariants = cva(
  [
    'flex w-full appearance-none border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900',
    'transition-all duration-150 ease-in-out cursor-pointer',
    'focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-opacity-20 focus:outline-none',
    'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50',
    'aria-invalid:border-error-500 aria-invalid:ring-error-500 aria-invalid:ring-opacity-20',
  ],
  {
    variants: {
      size: {
        sm: 'h-8 px-2 text-xs',
        md: 'h-9 px-3 text-sm',
        lg: 'h-10 px-4 text-base',
      },
      variant: {
        default: '',
        success: 'border-success-500 ring-success-500 ring-opacity-20',
        error: 'border-error-500 ring-error-500 ring-opacity-20',
      },
    },
    defaultVariants: {
      size: 'md',
      variant: 'default',
    },
  }
);

export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectProps
  extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'size'>,
    VariantProps<typeof selectVariants> {
  label?: string;
  helperText?: string;
  error?: string;
  options: SelectOption[];
  placeholder?: string;
  loading?: boolean;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      className,
      size,
      variant,
      label,
      helperText,
      error,
      options,
      placeholder,
      loading,
      id,
      disabled,
      'aria-invalid': ariaInvalid,
      ...props
    },
    ref
  ) => {
    const reactId = React.useId();
    const selectId = id || `select-${reactId}`;
    const hasError = Boolean(error);
    const actualVariant = hasError ? 'error' : variant;
    const isInvalid = ariaInvalid || hasError;

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={selectId}
            className="block text-sm font-medium text-gray-700"
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          <select
            className={cn(
              selectVariants({ size, variant: actualVariant, className }),
              'pr-10'
            )}
            ref={ref}
            id={selectId}
            disabled={disabled || loading}
            aria-invalid={isInvalid}
            aria-describedby={
              error ? `${selectId}-error` : helperText ? `${selectId}-helper` : undefined
            }
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option
                key={option.value}
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>
          
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
            {loading ? (
              <div className="w-4 h-4 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </div>
        </div>
        
        {error && (
          <p
            id={`${selectId}-error`}
            className="text-sm text-error-600"
            role="alert"
          >
            {error}
          </p>
        )}
        
        {helperText && !error && (
          <p
            id={`${selectId}-helper`}
            className="text-sm text-gray-500"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';

export { Select, selectVariants };