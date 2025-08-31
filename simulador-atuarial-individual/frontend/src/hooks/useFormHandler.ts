import { useCallback } from 'react';
import type { SimulatorState } from '../types';

interface FormHandlerProps {
  onStateChange: (updates: Partial<SimulatorState>) => void;
}

export const useFormHandler = ({ onStateChange }: FormHandlerProps) => {
  const handleInputChange = useCallback((field: keyof SimulatorState, value: any) => {
    onStateChange({ [field]: value });
  }, [onStateChange]);

  const handleMultipleChanges = useCallback((changes: Partial<SimulatorState>) => {
    onStateChange(changes);
  }, [onStateChange]);

  const createFieldHandler = useCallback((field: keyof SimulatorState) => {
    return (value: any) => handleInputChange(field, value);
  }, [handleInputChange]);

  return {
    handleInputChange,
    handleMultipleChanges,
    createFieldHandler,
  };
};