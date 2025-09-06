import React, { useMemo, useCallback, useState } from 'react';
import { cn } from '../../lib/utils';
import styles from './RangeSlider.module.css';

export interface RangeSliderProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
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
    const sliderId = useMemo(() => id || `slider-${Math.random().toString(36).substr(2, 9)}`, [id]);
    const hasError = Boolean(error);
    
    // Estado para controlar edição manual
    const [isEditing, setIsEditing] = useState(false);
    const [textValue, setTextValue] = useState('');

    const handleSliderChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
      onChange(parseFloat(event.target.value));
    }, [onChange]);

    // Parser para remover formatação e extrair número
    const parseValue = useCallback((text: string): number => {
      // Remove tudo exceto números, vírgula e ponto
      const cleaned = text.replace(/[^\d,.-]/g, '');
      // Substitui vírgula por ponto para parsing
      const normalized = cleaned.replace(',', '.');
      const parsed = parseFloat(normalized);
      return isNaN(parsed) ? value : parsed;
    }, [value]);

    // Handlers para edição manual
    const handleTextFocus = useCallback(() => {
      setIsEditing(true);
      setTextValue(value.toString());
    }, [value]);

    const handleTextChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
      setTextValue(event.target.value);
    }, []);

    const handleTextBlur = useCallback(() => {
      const newValue = parseValue(textValue);
      // Permite valores além dos limites do slider na entrada manual
      onChange(newValue);
      setIsEditing(false);
    }, [textValue, parseValue, onChange]);

    const handleTextKeyDown = useCallback((event: React.KeyboardEvent<HTMLInputElement>) => {
      if (event.key === 'Enter') {
        event.currentTarget.blur();
      } else if (event.key === 'Escape') {
        setIsEditing(false);
      }
    }, []);

    return (
      <div className="w-full">
        <label
          htmlFor={sliderId}
          className="block text-sm font-medium text-gray-700"
        >
          {label}
        </label>
        <div className="mt-2 flex items-center space-x-4">
          <input
            ref={ref}
            type="range"
            id={sliderId}
            min={min}
            max={max}
            step={step}
            value={Math.max(min, Math.min(max, value))}
            onChange={handleSliderChange}
            disabled={disabled}
            className={styles.rangeSlider}
            aria-describedby={
              error ? `${sliderId}-error` : helperText ? `${sliderId}-helper` : ariaDescribedBy
            }
            {...props}
          />
          <div className="w-24 text-right">
            <input
              type="text"
              value={isEditing ? textValue : `${formatDisplay(value)}${suffix}`}
              onFocus={handleTextFocus}
              onChange={handleTextChange}
              onBlur={handleTextBlur}
              onKeyDown={handleTextKeyDown}
              disabled={disabled}
              className="w-full text-sm text-gray-700 border border-gray-300 rounded-md py-1 px-2 text-center cursor-text hover:border-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>
    );
  }
));

RangeSlider.displayName = 'RangeSlider';

export { RangeSlider };
