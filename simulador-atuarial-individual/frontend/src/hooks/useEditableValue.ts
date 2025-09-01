import { useState, useCallback, useRef, useEffect } from 'react';

interface UseEditableValueProps {
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  formatDisplay?: (value: number) => string;
  disabled?: boolean;
}

interface UseEditableValueReturn {
  isEditing: boolean;
  tempValue: string;
  hasError: boolean;
  errorMessage: string;
  displayValue: string;
  inputRef: React.RefObject<HTMLInputElement>;
  handleClick: () => void;
  handleInputChange: (value: string) => void;
  handleKeyDown: (e: React.KeyboardEvent) => void;
  handleBlur: () => void;
  handleFocus: () => void;
}

export const useEditableValue = ({
  value,
  min,
  max,
  step,
  onChange,
  formatDisplay = (v) => v.toString(),
  disabled = false,
}: UseEditableValueProps): UseEditableValueReturn => {
  const [isEditing, setIsEditing] = useState(false);
  const [tempValue, setTempValue] = useState('');
  const [hasError, setHasError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const validateValue = useCallback((inputValue: string): { isValid: boolean; parsedValue: number; error: string } => {
    if (!inputValue.trim()) {
      return { isValid: false, parsedValue: value, error: 'Valor não pode estar vazio' };
    }

    const parsed = parseFloat(inputValue.replace(',', '.'));
    
    if (isNaN(parsed)) {
      return { isValid: false, parsedValue: value, error: 'Valor deve ser um número' };
    }

    if (parsed < min) {
      return { isValid: false, parsedValue: value, error: `Valor mínimo é ${formatDisplay(min)}` };
    }

    if (parsed > max) {
      return { isValid: false, parsedValue: value, error: `Valor máximo é ${formatDisplay(max)}` };
    }

    const roundedValue = Math.round(parsed / step) * step;
    return { isValid: true, parsedValue: roundedValue, error: '' };
  }, [min, max, step, value, formatDisplay]);

  const applyValue = useCallback((inputValue: string) => {
    const validation = validateValue(inputValue);
    
    if (validation.isValid) {
      onChange(validation.parsedValue);
      setHasError(false);
      setErrorMessage('');
      setIsEditing(false);
    } else {
      setHasError(true);
      setErrorMessage(validation.error);
    }
  }, [validateValue, onChange]);

  const cancelEditing = useCallback(() => {
    setIsEditing(false);
    setHasError(false);
    setErrorMessage('');
    setTempValue('');
  }, []);

  const handleClick = useCallback(() => {
    if (disabled) return;
    
    setIsEditing(true);
    setTempValue(value.toString());
    setHasError(false);
    setErrorMessage('');
  }, [disabled, value]);

  const handleInputChange = useCallback((inputValue: string) => {
    setTempValue(inputValue);
    
    if (hasError) {
      const validation = validateValue(inputValue);
      if (validation.isValid) {
        setHasError(false);
        setErrorMessage('');
      }
    }
  }, [hasError, validateValue]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      applyValue(tempValue);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      cancelEditing();
    }
  }, [tempValue, applyValue, cancelEditing]);

  const handleBlur = useCallback(() => {
    if (!hasError && tempValue.trim()) {
      applyValue(tempValue);
    } else {
      cancelEditing();
    }
  }, [hasError, tempValue, applyValue, cancelEditing]);

  const handleFocus = useCallback(() => {
    if (inputRef.current) {
      inputRef.current.select();
    }
  }, []);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const displayValue = isEditing ? tempValue : formatDisplay(value);

  return {
    isEditing,
    tempValue,
    hasError,
    errorMessage,
    displayValue,
    inputRef,
    handleClick,
    handleInputChange,
    handleKeyDown,
    handleBlur,
    handleFocus,
  };
};