import React, { useMemo, useCallback } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';
import { useEditableValue } from '../../hooks';
import styles from './RangeSlider.module.css';

const sliderVariants = cva(
  [
    'w-full h-[2px] bg-gray-200 rounded-full appearance-none cursor-pointer',
    'transition-all duration-150 ease-in-out',
    'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-20',
    'disabled:cursor-not-allowed disabled:opacity-50',
  ],
  {
    variants: {
      size: {
        sm: 'h-[2px]',
        md: 'h-[2px]', 
        lg: 'h-1',
      },
    },
    defaultVariants: {
      size: 'md',
    },
  }
);

export interface RangeSliderProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'onChange'>,
    VariantProps<typeof sliderVariants> {
  label?: string | React.ReactNode;
  helperText?: string;
  error?: string;
  tooltip?: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  formatDisplay?: (value: number) => string;
  suffix?: string;
  showMinMax?: boolean; // Deprecated - não usado na inspiração
}

const RangeSlider = React.memo(React.forwardRef<HTMLInputElement, RangeSliderProps>(
  (
    {
      className,
      size,
      label,
      helperText,
      error,
      tooltip,
      value,
      min,
      max,
      step,
      onChange,
      formatDisplay = (v) => v.toString(),
      suffix = '',
      showMinMax = true,
      id,
      disabled,
      'aria-describedby': ariaDescribedBy,
      ...props
    },
    ref
  ) => {
    // Memoizar ID para evitar recriação desnecessária
    const sliderId = useMemo(() => id || `slider-${Math.random().toString(36).substr(2, 9)}`, [id]);
    const hasError = Boolean(error);
    // Percentage não mais necessário - slider simples sem gradiente

    const handleChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
      onChange(parseFloat(event.target.value));
    }, [onChange]);

    // Hook para gerenciar edição de valor
    const editableValue = useEditableValue({
      value,
      min,
      max,
      step,
      onChange,
      formatDisplay,
      disabled,
    });

    // Percentage para trilho progressivo como na inspiração
    const percentage = useMemo(() => ((value - min) / (max - min)) * 100, [value, min, max]);
    
    // Background style com trilho progressivo
    const backgroundStyle = useMemo(() => ({
      background: `linear-gradient(to right, #13a4ec 0%, #13a4ec ${percentage}%, #e5e7eb ${percentage}%, #e5e7eb 100%)`
    }), [percentage]);

    return (
      <div className="space-y-6">
        {/* Horizontal Layout - Inspiration Style */}
        <div className="flex items-center gap-4">
          {/* Label */}
          {label && (
            <div className="min-w-[180px]" title={tooltip}>
              <label
                htmlFor={sliderId}
                className="block text-sm font-medium text-[#111618]"
              >
                {label}
              </label>
            </div>
          )}
          
          {/* Slider Track */}
          <div className="flex-1 relative flex items-center">
            <input
              ref={ref}
              type="range"
              id={sliderId}
              min={min}
              max={max}
              step={step}
              value={value}
              onChange={handleChange}
              disabled={disabled}
              className={cn(
                sliderVariants({ size }),
                styles.rangeSlider,
                hasError && 'border-error-500 ring-error-500',
                className
              )}
              style={backgroundStyle}
              aria-describedby={
                error ? `${sliderId}-error` : helperText ? `${sliderId}-helper` : ariaDescribedBy
              }
              {...props}
            />
          </div>
          
          {/* Value Display - Right side */}
          <div className="relative min-w-[70px] flex justify-end">
            {editableValue.isEditing ? (
              <input
                ref={editableValue.inputRef}
                type="text"
                value={editableValue.tempValue}
                onChange={(e) => editableValue.handleInputChange(e.target.value)}
                onKeyDown={editableValue.handleKeyDown}
                onBlur={editableValue.handleBlur}
                onFocus={editableValue.handleFocus}
                className={cn(
                  'bg-white text-[#617c89] px-2 py-1 rounded text-sm border text-right min-w-0',
                  editableValue.hasError 
                    ? 'border-red-300 ring-1 ring-red-300' 
                    : 'border-gray-200 focus:border-[#13a4ec] focus:ring-1 focus:ring-[#13a4ec] focus:ring-opacity-20'
                )}
                style={{ width: 'auto', minWidth: '70px' }}
              />
            ) : (
              <button
                type="button"
                onClick={editableValue.handleClick}
                disabled={disabled}
                className={cn(
                  'text-[#617c89] text-sm font-medium transition-colors text-right',
                  !disabled && 'hover:text-[#13a4ec] cursor-pointer',
                  disabled && 'cursor-not-allowed opacity-50'
                )}
              >
                {editableValue.displayValue}{suffix}
              </button>
            )}
            
            {editableValue.hasError && editableValue.errorMessage && (
              <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-1 px-2 py-1 bg-red-600 text-white text-xs rounded whitespace-nowrap z-10">
                {editableValue.errorMessage}
              </div>
            )}
          </div>
        </div>
        
        {/* Error Message */}
        {error && (
          <p
            id={`${sliderId}-error`}
            className="text-sm text-error-600 ml-[184px]"
            role="alert"
          >
            {error}
          </p>
        )}
        
        {/* Helper Text */}
        {helperText && !error && (
          <p
            id={`${sliderId}-helper`}
            className="text-sm text-gray-500 ml-[184px]"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
));

RangeSlider.displayName = 'RangeSlider';

export { RangeSlider, sliderVariants };
