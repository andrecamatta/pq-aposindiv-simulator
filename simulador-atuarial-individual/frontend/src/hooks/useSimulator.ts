import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { SimulatorState, SimulatorResults, MortalityTable } from '../types';
import { apiService, WebSocketClient } from '../services/api';

export const useSimulator = () => {
  const [state, setState] = useState<SimulatorState | null>(null);
  const [results, setResults] = useState<SimulatorResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  
  const wsClient = useRef<WebSocketClient | null>(null);
  const debounceTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Carregar estado padrão
  const { data: defaultState } = useQuery({
    queryKey: ['defaultState'],
    queryFn: apiService.getDefaultState,
  });

  // Carregar tábuas de mortalidade
  const { data: mortalityTables } = useQuery({
    queryKey: ['mortalityTables'],
    queryFn: apiService.getMortalityTables,
  });

  // Inicializar WebSocket
  useEffect(() => {
    if (!wsClient.current) {
      wsClient.current = new WebSocketClient();
      
      // Configurar handlers
      wsClient.current.on('calculation_started', (data) => {
        setLoading(true);
        setError(null);
      });
      
      wsClient.current.on('results_update', (data) => {
        setResults(data);
        setLoading(false);
      });
      
      wsClient.current.on('sensitivity_update', () => {
        // Atualizar dados de sensibilidade se necessário
      });
      
      wsClient.current.on('calculation_completed', () => {
        setLoading(false);
      });
      
      wsClient.current.on('error', (data) => {
        setError(data.message || 'Erro desconhecido');
        setLoading(false);
      });
      
      wsClient.current.on('pong', () => {
        // Pong received
      });
      
      // Conectar
      wsClient.current.connect()
        .then(() => setConnected(true))
        .catch(() => {
          setConnected(false);
        });
    }

    return () => {
      if (wsClient.current) {
        wsClient.current.disconnect();
        wsClient.current = null;
      }
    };
  }, []);

  const lastCalculatedStateRef = useRef<string | null>(null);

  // Função para determinar o delay do debounce baseado no tipo de mudança
  const getDebounceDelay = useCallback((currentState: SimulatorState, previousState: SimulatorState | null) => {
    if (!previousState) return 500;

    // Configurações técnicas que podem ter delay maior (não afetam cálculos imediatos)
    const technicalFields = [
      'mortality_table', 'calculation_method', 'payment_timing', 
      'salary_months_per_year', 'benefit_months_per_year'
    ];

    // Configurações que afetam cálculos e precisam de feedback mais rápido
    const immediateFields = [
      'age', 'salary', 'target_benefit', 'target_replacement_rate',
      'contribution_rate', 'accrual_rate', 'retirement_age'
    ];

    // Verificar quais campos mudaram
    const changedFields = Object.keys(currentState).filter(
      key => currentState[key as keyof SimulatorState] !== previousState[key as keyof SimulatorState]
    );

    // Se apenas campos técnicos mudaram, usar delay maior
    if (changedFields.length > 0 && changedFields.every(field => technicalFields.includes(field))) {
      return 1000; // 1 segundo para configs técnicas
    }

    // Se campos de custo administrativo mudaram, delay médio
    if (changedFields.some(field => ['admin_fee_rate', 'loading_fee_rate'].includes(field))) {
      return 750; // 750ms para custos administrativos
    }

    // Para outros campos, delay padrão
    return 500;
  }, []);

  // Função debounced para cálculo com delay inteligente
  const debouncedCalculate = useCallback((currentState: SimulatorState, previousState: SimulatorState | null = null) => {
    // Verificar se o estado realmente mudou para evitar cálculos desnecessários
    const currentStateString = JSON.stringify(currentState);
    if (lastCalculatedStateRef.current === currentStateString) {
      return;
    }

    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    const delay = getDebounceDelay(currentState, previousState);

    debounceTimeoutRef.current = setTimeout(() => {
      const preparedState = { ...currentState };
      
      if (preparedState.benefit_target_mode === 'REPLACEMENT_RATE') {
        preparedState.target_benefit = undefined;
      } else {
        preparedState.target_replacement_rate = undefined;
      }

      lastCalculatedStateRef.current = JSON.stringify(preparedState);
      setLoading(true);
      apiService.calculate(preparedState)
        .then(setResults)
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }, delay);
  }, [getDebounceDelay]);

  // Inicializa o estado com os valores padrão da API.
  useEffect(() => {
    if (defaultState && !state) {
      setState(defaultState);
    }
  }, [defaultState, state]);

  const previousStateRef = useRef<SimulatorState | null>(null);

  // Efeito principal que reage a QUALQUER mudança no estado e dispara o cálculo.
  useEffect(() => {
    // Só executa se o estado já estiver inicializado.
    if (state) {
      debouncedCalculate(state, previousStateRef.current);
      previousStateRef.current = state;
    }
  }, [state, debouncedCalculate]);

  // Função para atualizar o estado a partir dos componentes.
  const updateState = useCallback((updates: Partial<SimulatorState>) => {
    setState(prevState => {
      if (!prevState) return null; // Não faz nada se o estado ainda não foi inicializado
      return {
        ...prevState,
        ...updates,
        last_update: new Date().toISOString()
      };
    });
  }, []);

  // Resetar para estado padrão
  const resetToDefault = useCallback(() => {
    if (defaultState) {
      setState(defaultState);
      setResults(null);
      setError(null);
    }
  }, [defaultState]);

  // Ping WebSocket
  const ping = useCallback(() => {
    if (wsClient.current && wsClient.current.isConnected()) {
      wsClient.current.ping();
    }
  }, []);

  // Recalcular manualmente
  const recalculate = useCallback(() => {
    if (state) {
      debouncedCalculate(state);
    }
  }, [state, debouncedCalculate]);


  return {
    // Estado
    state,
    results,
    loading,
    error,
    connected,
    
    // Dados auxiliares
    mortalityTables: mortalityTables || [],
    
    // Ações
    updateState,
    resetToDefault,
    recalculate,
    ping,
    
    // Utilities
    isReady: !!state && !!mortalityTables,
  };
};