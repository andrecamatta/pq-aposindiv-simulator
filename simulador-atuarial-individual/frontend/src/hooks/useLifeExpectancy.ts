import { useState, useEffect, useCallback } from 'react';
import { useToast } from './useToast';

interface LifeExpectancyParams {
  age: number;
  gender: 'M' | 'F';
  mortalityTable: string;
  aggravation: number; // Percentual de suavização aplicado na tábua
}

interface LifeExpectancyData {
  life_expectancy: number;
  expected_death_age: number;
  current_age: number;
  parameters: {
    gender: string;
    mortality_table: string;
    actual_table_used?: string;
    smoothing_percent?: number;
    aggravation_percent?: number;
  };
}

interface UseLifeExpectancyReturn {
  data: LifeExpectancyData | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const useLifeExpectancy = (params: LifeExpectancyParams): UseLifeExpectancyReturn => {
  const [data, setData] = useState<LifeExpectancyData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { showToast } = useToast();

  const fetchLifeExpectancy = useCallback(async () => {
    if (!params.age || !params.gender || !params.mortalityTable) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams({
        age: params.age.toString(),
        gender: params.gender,
        mortality_table: params.mortalityTable,
        aggravation: params.aggravation.toString() // API espera o termo "aggravation"
      });

      const response = await fetch(`${API_BASE_URL}/life-expectancy?${queryParams}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.success && result.data) {
        setData(result.data);
      } else {
        throw new Error(result.message || 'Erro ao calcular expectativa de vida');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setError(errorMessage);
      // Não mostrar toast para erro de expectativa de vida (não é crítico)
      console.warn('Erro ao buscar expectativa de vida:', err);
    } finally {
      setLoading(false);
    }
  }, [params.age, params.gender, params.mortalityTable, params.aggravation]);

  // Debounce: aguardar 500ms após última mudança de parâmetros
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchLifeExpectancy();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [fetchLifeExpectancy]);

  const refetch = useCallback(() => {
    fetchLifeExpectancy();
  }, [fetchLifeExpectancy]);

  return {
    data,
    loading,
    error,
    refetch
  };
};
