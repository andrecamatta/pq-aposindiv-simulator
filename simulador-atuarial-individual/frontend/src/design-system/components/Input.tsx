import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const inputVariants = cva(
  [
    'flex w-full border border-[#dbe2e6] bg-white px-4 py-3 text-base text-[#111618] placeholder:text-[#9ca3af]',
    'transition-all duration-150 ease-in-out rounded-md',
    'focus:border-[#13a4ec] focus:ring-1 focus:ring-[#13a4ec] focus:ring-opacity-20 focus:outline-none',
    'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50',
    'aria-invalid:border-red-500 aria-invalid:ring-red-500 aria-invalid:ring-opacity-20',
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

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  label?: string;
  helperText?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  loading?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      type = 'text',
      size,
      variant,
      label,
      helperText,
      error,
      leftIcon,
      rightIcon,
      loading,
      id,
      disabled,
      'aria-invalid': ariaInvalid,
      ...props
    },
    ref
  ) => {
    const reactId = React.useId();
    const inputId = id || `input-${reactId}`;
    const hasError = Boolean(error);
    const actualVariant = hasError ? 'error' : variant;
    const isInvalid = ariaInvalid || hasError;

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-[#111618] mb-2"
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {leftIcon}
            </div>
          )}
          
          <input
            type={type}
            className={cn(
              inputVariants({ size, variant: actualVariant, className }),
              leftIcon && 'pl-10',
              (rightIcon || loading) && 'pr-10'
            )}
            ref={ref}
            id={inputId}
            disabled={disabled || loading}
            aria-invalid={isInvalid}
            aria-describedby={
              error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
            }
            {...props}
          />
          
          {(rightIcon || loading) && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
              {loading ? (
                <div className="w-4 h-4 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin" />
              ) : (
                rightIcon
              )}
            </div>
          )}
        </div>
        
        {error && (
          <p
            id={`${inputId}-error`}
            className="text-sm text-error-600"
            role="alert"
          >
            {error}
          </p>
        )}
        
        {helperText && !error && (
          <p
            id={`${inputId}-helper`}
            className="text-sm text-gray-500"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input, inputVariants };