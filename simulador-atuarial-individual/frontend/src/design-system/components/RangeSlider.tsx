import React, { useMemo, useCallback } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';
import { HelpCircle } from 'lucide-react';
import { Tooltip } from './Tooltip';
import { useEditableValue } from '../../hooks';
import styles from './RangeSlider.module.css';

const sliderVariants = cva(
  [
    'w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer',
    'transition-all duration-150 ease-in-out',
    'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-20',
    'disabled:cursor-not-allowed disabled:opacity-50',
  ],
  {
    variants: {
      size: {
        sm: 'h-1',
        md: 'h-2',
        lg: 'h-3',
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
  label?: string;
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
  showMinMax?: boolean;
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
    const percentage = useMemo(() => ((value - min) / (max - min)) * 100, [value, min, max]);

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

    // Memoizar estilo do background para evitar recalculação desnecessária
    const backgroundStyle = useMemo(() => ({
      background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${percentage}%, #e5e7eb ${percentage}%, #e5e7eb 100%)`
    }), [percentage]);

    return (
      <div className="space-y-3">
        {/* Label and Value */}
        {label && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <label
                htmlFor={sliderId}
                className="text-sm font-medium text-gray-700"
              >
                {label}
              </label>
              {tooltip && (
                <Tooltip content={tooltip}>
                  <HelpCircle className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help" />
                </Tooltip>
              )}
            </div>
            
            <div className="relative">
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
                    'bg-primary-50 text-primary-700 px-3 py-1 rounded-md text-sm font-semibold border text-center min-w-0',
                    editableValue.hasError 
                      ? 'border-error-500 ring-1 ring-error-500 ring-opacity-20' 
                      : 'border-primary-200 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 focus:ring-opacity-20'
                  )}
                  style={{ width: 'auto', minWidth: '60px' }}
                />
              ) : (
                <button
                  type="button"
                  onClick={editableValue.handleClick}
                  disabled={disabled}
                  className={cn(
                    'bg-primary-50 text-primary-700 px-3 py-1 rounded-md text-sm font-semibold border border-primary-200 transition-colors',
                    !disabled && 'hover:bg-primary-100 hover:border-primary-300 cursor-pointer',
                    disabled && 'cursor-not-allowed opacity-50'
                  )}
                >
                  {editableValue.displayValue}{suffix}
                </button>
              )}
              
              {editableValue.hasError && editableValue.errorMessage && (
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-1 px-2 py-1 bg-error-600 text-white text-xs rounded whitespace-nowrap z-10">
                  {editableValue.errorMessage}
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Slider Track */}
        <div className="relative">
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
        
        {/* Min/Max Labels */}
        {showMinMax && (
          <div className="flex justify-between text-xs text-gray-500">
            <span>{formatDisplay(min)}{suffix}</span>
            <span>{formatDisplay(max)}{suffix}</span>
          </div>
        )}
        
        {/* Error Message */}
        {error && (
          <p
            id={`${sliderId}-error`}
            className="text-sm text-error-600"
            role="alert"
          >
            {error}
          </p>
        )}
        
        {/* Helper Text */}
        {helperText && !error && (
          <p
            id={`${sliderId}-helper`}
            className="text-sm text-gray-500"
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