import React, { useRef, useState, useCallback } from 'react';

interface CustomSliderProps {
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
}

const CustomSlider: React.FC<CustomSliderProps> = ({
  label,
  value,
  min,
  max,
  step,
  onChange,
  suffix = '',
  tooltip = '',
  disabled = false,
  formatDisplay = (v) => v.toString()
}) => {
  const sliderRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const getValueFromPosition = useCallback((clientX: number) => {
    if (!sliderRef.current) return value;
    
    const rect = sliderRef.current.getBoundingClientRect();
    const percentage = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    const rawValue = min + (max - min) * percentage;
    return Math.round(rawValue / step) * step;
  }, [min, max, step, value]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (disabled) return;
    
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
    
    const newValue = getValueFromPosition(e.clientX);
    onChange(newValue);
    
    // Add cursor grabbing state
    document.body.style.cursor = 'grabbing';
  }, [disabled, getValueFromPosition, onChange]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging || disabled) return;
    
    const newValue = getValueFromPosition(e.clientX);
    onChange(newValue);
  }, [isDragging, disabled, getValueFromPosition, onChange]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    document.body.style.cursor = 'default';
  }, []);

  React.useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className="space-y-3 bg-gray-50 p-4 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <label className="text-sm font-semibold text-gray-800">{label}</label>
          {tooltip && (
            <div className="relative group">
              <span className="w-4 h-4 rounded-full bg-blue-100 text-xs flex items-center justify-center cursor-help text-blue-600 font-bold border border-blue-200">?</span>
              <div className="invisible group-hover:visible absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 text-xs text-white bg-gray-900 rounded-lg whitespace-nowrap z-10 shadow-lg">
                {tooltip}
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-900"></div>
              </div>
            </div>
          )}
        </div>
        <span className="text-sm font-bold text-white bg-gradient-to-r from-indigo-500 to-purple-600 px-3 py-1 rounded-lg shadow-sm">
          {formatDisplay(value)}{suffix}
        </span>
      </div>

      <div className="relative">
        <div
          ref={sliderRef}
          className={`relative h-4 bg-gradient-to-r from-gray-100 to-gray-200 rounded-full border border-gray-300 shadow-inner ${!disabled ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'}`}
          onMouseDown={handleMouseDown}
        >
          <div 
            className="absolute h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-600 rounded-full shadow-sm" 
            style={{ width: `${percentage}%` }}
          />
          <div
            className={`absolute w-6 h-6 bg-white border-3 border-indigo-500 rounded-full shadow-lg transform -translate-y-1 ${
              isDragging ? 'scale-110 border-indigo-700 shadow-xl' : 'hover:scale-105 hover:shadow-lg'
            } transition-all duration-150 ${!disabled ? 'cursor-grab' : 'cursor-not-allowed'}`}
            style={{ left: `calc(${percentage}% - 12px)` }}
          >
            <div className="w-2 h-2 bg-indigo-500 rounded-full absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"></div>
          </div>
        </div>
      </div>

      <div className="flex justify-between text-xs text-gray-500 font-medium">
        <span>{formatDisplay(min)}{suffix}</span>
        <span>{formatDisplay(max)}{suffix}</span>
      </div>
    </div>
  );
};

export default CustomSlider;