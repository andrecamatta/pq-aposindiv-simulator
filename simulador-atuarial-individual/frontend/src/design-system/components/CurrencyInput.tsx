import React, { forwardRef } from 'react';
import { NumericFormat, type NumericFormatProps } from 'react-number-format';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';
import { inputVariants } from './Input'; // Assuming inputVariants are exported from Input.tsx

const currencyInputVariants = inputVariants; // Reuse input variants for consistency

export interface CurrencyInputProps
  extends Omit<NumericFormatProps, 'value' | 'onValueChange' | 'size'>, // Omit 'size' to prevent conflict
    VariantProps<typeof currencyInputVariants> {
  label?: string;
  helperText?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  loading?: boolean;
  value?: number | null; // Our specific value type
  onValueChange?: (value: number | null) => void; // Our specific onValueChange type
}

const CurrencyInput = forwardRef<HTMLInputElement, CurrencyInputProps>(
  (
    {
      className,
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
      value,
      onValueChange,
      'aria-invalid': ariaInvalid,
      ...props
    },
    ref
  ) => {
    const reactId = React.useId();
    const inputId = id || `currency-input-${reactId}`;
    const hasError = Boolean(error);
    const actualVariant = hasError ? 'error' : variant;
    const isInvalid = ariaInvalid || hasError;

    const inputClasses = cn(
      currencyInputVariants({ size, variant: actualVariant, className }),
      leftIcon && 'pl-10',
      (rightIcon || loading) && 'pr-16'
    );

    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {leftIcon}
            </div>
          )}
          
          <NumericFormat
            thousandSeparator="."
            decimalSeparator=","
            prefix="R$ "
            allowNegative={false}
            decimalScale={2}
            fixedDecimalScale={true}
            getInputRef={ref}
            className={inputClasses}
            id={inputId}
            disabled={disabled || loading}
            aria-invalid={isInvalid}
            aria-describedby={
              error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
            }
            value={value}
            onValueChange={(values) => onValueChange && onValueChange(values.floatValue ?? null)}
            {...props}
          />
          
          {(rightIcon || loading) && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
              {loading ? (
                <div className="w-4 h-4 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin" />
              ) : (
                rightIcon
              )}
            </div>
          )}
        </div>
        
        {error && (
          <p id={`${inputId}-error`} className="text-sm text-error-600" role="alert">
            {error}
          </p>
        )}
        
        {helperText && !error && (
          <p id={`${inputId}-helper`} className="text-sm text-gray-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

CurrencyInput.displayName = 'CurrencyInput';

export { CurrencyInput };
export default CurrencyInput;
