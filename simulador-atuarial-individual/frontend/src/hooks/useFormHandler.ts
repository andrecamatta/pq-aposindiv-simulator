import { useCallback, useMemo, useRef } from 'react';
import type { SimulatorState } from '../types';

interface FormHandlerProps {
  onStateChange: (updates: Partial<SimulatorState>) => void;
}

export const useFormHandler = ({ onStateChange }: FormHandlerProps) => {
  // Cache dos field handlers para evitar recriações desnecessárias
  const fieldHandlersRef = useRef<Map<keyof SimulatorState, (value: any) => void>>(new Map());

  const handleInputChange = useCallback((field: keyof SimulatorState, value: any) => {
    onStateChange({ [field]: value });
  }, [onStateChange]);

  const handleMultipleChanges = useCallback((changes: Partial<SimulatorState>) => {
    onStateChange(changes);
  }, [onStateChange]);

  const createFieldHandler = useCallback((field: keyof SimulatorState) => {
    // Retornar handler cacheado se já existe
    if (fieldHandlersRef.current.has(field)) {
      return fieldHandlersRef.current.get(field)!;
    }

    // Criar novo handler e cachear
    const handler = (value: any) => handleInputChange(field, value);
    fieldHandlersRef.current.set(field, handler);
    return handler;
  }, [handleInputChange]);

  // Criar handlers memoizados para campos comuns usados na aba técnica
  const memoizedHandlers = useMemo(() => ({
    mortality_table: createFieldHandler('mortality_table'),
    calculation_method: createFieldHandler('calculation_method'),
    payment_timing: createFieldHandler('payment_timing'),
    salary_months_per_year: createFieldHandler('salary_months_per_year'),
    benefit_months_per_year: createFieldHandler('benefit_months_per_year'),
    admin_fee_rate: createFieldHandler('admin_fee_rate'),
    loading_fee_rate: createFieldHandler('loading_fee_rate'),
  }), [createFieldHandler]);

  return {
    handleInputChange,
    handleMultipleChanges,
    createFieldHandler,
    ...memoizedHandlers,
  };
};