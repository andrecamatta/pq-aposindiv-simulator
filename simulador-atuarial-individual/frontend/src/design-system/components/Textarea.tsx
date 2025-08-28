import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const textareaVariants = cva(
  [
    'flex w-full border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400',
    'transition-all duration-150 ease-in-out resize-none',
    'focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-opacity-20 focus:outline-none',
    'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50',
    'aria-invalid:border-error-500 aria-invalid:ring-error-500 aria-invalid:ring-opacity-20',
  ],
  {
    variants: {
      size: {
        sm: 'px-2 py-1 text-xs min-h-[64px]',
        md: 'px-3 py-2 text-sm min-h-[80px]',
        lg: 'px-4 py-3 text-base min-h-[96px]',
      },
      variant: {
        default: '',
        success: 'border-success-500 ring-success-500 ring-opacity-20',
        error: 'border-error-500 ring-error-500 ring-opacity-20',
      },
      resize: {
        none: 'resize-none',
        vertical: 'resize-y',
        horizontal: 'resize-x',
        both: 'resize',
      },
    },
    defaultVariants: {
      size: 'md',
      variant: 'default',
      resize: 'vertical',
    },
  }
);

export interface TextareaProps
  extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'size'>,
    VariantProps<typeof textareaVariants> {
  label?: string;
  helperText?: string;
  error?: string;
  showCharCount?: boolean;
  maxLength?: number;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      size,
      variant,
      resize,
      label,
      helperText,
      error,
      showCharCount,
      maxLength,
      value,
      id,
      disabled,
      'aria-invalid': ariaInvalid,
      ...props
    },
    ref
  ) => {
    const reactId = React.useId();
    const textareaId = id || `textarea-${reactId}`;
    const hasError = Boolean(error);
    const actualVariant = hasError ? 'error' : variant;
    const isInvalid = ariaInvalid || hasError;
    
    const charCount = typeof value === 'string' ? value.length : 0;
    const showCount = showCharCount && (maxLength || charCount > 0);

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-gray-700"
          >
            {label}
          </label>
        )}
        
        <textarea
          className={cn(
            textareaVariants({ size, variant: actualVariant, resize, className })
          )}
          ref={ref}
          id={textareaId}
          disabled={disabled}
          aria-invalid={isInvalid}
          aria-describedby={
            error ? `${textareaId}-error` : helperText ? `${textareaId}-helper` : undefined
          }
          maxLength={maxLength}
          value={value}
          {...props}
        />
        
        <div className="flex justify-between">
          <div className="flex-1">
            {error && (
              <p
                id={`${textareaId}-error`}
                className="text-sm text-error-600"
                role="alert"
              >
                {error}
              </p>
            )}
            
            {helperText && !error && (
              <p
                id={`${textareaId}-helper`}
                className="text-sm text-gray-500"
              >
                {helperText}
              </p>
            )}
          </div>
          
          {showCount && (
            <div className="text-xs text-gray-500 ml-2">
              {charCount}
              {maxLength && `/${maxLength}`}
            </div>
          )}
        </div>
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export { Textarea, textareaVariants };