import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';
import { HelpCircle } from 'lucide-react';
import { Tooltip } from './Tooltip';

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

const RangeSlider = React.forwardRef<HTMLInputElement, RangeSliderProps>(
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
    const sliderId = id || `slider-${React.useId()}`;
    const hasError = Boolean(error);
    const percentage = ((value - min) / (max - min)) * 100;

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      onChange(parseFloat(event.target.value));
    };

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
            
            <div className="bg-primary-50 text-primary-700 px-3 py-1 rounded-md text-sm font-semibold border border-primary-200">
              {formatDisplay(value)}{suffix}
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
              hasError && 'border-error-500 ring-error-500',
              className
            )}
            style={{
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${percentage}%, #e5e7eb ${percentage}%, #e5e7eb 100%)`
            }}
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
        
        {/* Custom Styles for Thumb */}
        <style jsx>{`
          input[type="range"]::-webkit-slider-thumb {
            appearance: none;
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: #ffffff;
            border: 2px solid #3b82f6;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            transition: all 0.15s ease;
          }
          
          input[type="range"]::-webkit-slider-thumb:hover {
            transform: scale(1.1);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            border-color: #2563eb;
          }
          
          input[type="range"]::-webkit-slider-thumb:active {
            transform: scale(1.05);
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
          }
          
          input[type="range"]::-moz-range-thumb {
            height: 20px;
            width: 20px;
            border-radius: 50%;
            background: #ffffff;
            border: 2px solid #3b82f6;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            transition: all 0.15s ease;
            border: none;
          }
          
          input[type="range"]::-moz-range-track {
            height: 8px;
            border-radius: 4px;
            background: #e5e7eb;
            border: none;
          }
          
          input[type="range"]:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          
          input[type="range"]:disabled::-webkit-slider-thumb {
            cursor: not-allowed;
          }
        `}</style>
      </div>
    );
  }
);

RangeSlider.displayName = 'RangeSlider';

export { RangeSlider, sliderVariants };