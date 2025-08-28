import React from 'react';
import { Info } from 'lucide-react';
import { cn } from '../../lib/utils';

interface SliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  suffix?: string;
  tooltip?: string;
  disabled?: boolean;
  formatDisplay?: (value: number) => string;
  className?: string;
}

const Slider: React.FC<SliderProps> = ({
  label,
  value,
  min,
  max,
  step,
  onChange,
  suffix = '',
  tooltip = '',
  disabled = false,
  formatDisplay = (v) => v.toString(),
  className
}) => {
  return (
    <div className={cn("space-y-4 p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200", className)}>
      {/* Header com label e valor */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <label className="text-base font-semibold text-slate-700">{label}</label>
          {tooltip && (
            <div className="group relative">
              <Info className="w-4 h-4 text-slate-400 hover:text-slate-600 cursor-help transition-colors" />
              <div className="absolute left-0 top-6 w-72 p-3 bg-slate-900 text-white text-sm rounded-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-20 shadow-xl">
                <div className="absolute -top-1 left-2 w-2 h-2 bg-slate-900 rotate-45"></div>
                {tooltip}
              </div>
            </div>
          )}
        </div>
        
        <div className="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-bold shadow-sm">
          {formatDisplay(value)}{suffix}
        </div>
      </div>

      {/* Slider HTML5 nativo estilizado */}
      <div className="px-1">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          disabled={disabled}
          className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer slider-thumb focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          style={{
            background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((value - min) / (max - min)) * 100}%, #e2e8f0 ${((value - min) / (max - min)) * 100}%, #e2e8f0 100%)`
          }}
        />
      </div>

      {/* Labels min/max */}
      <div className="flex justify-between text-xs text-slate-500 px-1">
        <span className="font-medium">{formatDisplay(min)}{suffix}</span>
        <span className="font-medium">{formatDisplay(max)}{suffix}</span>
      </div>

      {/* CSS para estilizar o thumb */}
      <style jsx>{`
        .slider-thumb::-webkit-slider-thumb {
          appearance: none;
          height: 22px;
          width: 22px;
          border-radius: 50%;
          background: #ffffff;
          border: 3px solid #3b82f6;
          cursor: pointer;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1), 0 0 0 0 rgba(59, 130, 246, 0.1);
          transition: all 0.15s ease;
        }

        .slider-thumb::-webkit-slider-thumb:hover {
          transform: scale(1.15);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), 0 0 0 4px rgba(59, 130, 246, 0.1);
          border-color: #2563eb;
        }

        .slider-thumb::-webkit-slider-thumb:active {
          transform: scale(1.1);
          box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3), 0 0 0 4px rgba(59, 130, 246, 0.2);
          border-color: #1d4ed8;
        }

        .slider-thumb::-moz-range-thumb {
          height: 22px;
          width: 22px;
          border-radius: 50%;
          background: #ffffff;
          border: 3px solid #3b82f6;
          cursor: pointer;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          transition: all 0.15s ease;
        }

        .slider-thumb::-moz-range-thumb:hover {
          transform: scale(1.15);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          border-color: #2563eb;
        }

        .slider-thumb:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
};

export default Slider;