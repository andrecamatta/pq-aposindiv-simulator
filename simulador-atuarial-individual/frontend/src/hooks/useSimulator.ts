import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { SimulatorState, SimulatorResults } from '../types';
import { apiService, WebSocketClient } from '../services/api';

export const useSimulator = () => {
  const [state, setState] = useState<SimulatorState | null>(null);
  const [results, setResults] = useState<SimulatorResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  const [lastPing, setLastPing] = useState<Date | null>(null);
  const [responseTime, setResponseTime] = useState<number | undefined>(undefined);
  
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

  // Health check periódico
  const performHealthCheck = useCallback(async () => {
    try {
      const startTime = performance.now();
      await apiService.healthCheck();
      const endTime = performance.now();
      const responseTimeMs = Math.round(endTime - startTime);

      setResponseTime(responseTimeMs);
      setLastPing(new Date());
      setConnectionStatus('connected');
      setConnected(true);
      return true;
    } catch (error) {
      setConnectionStatus('disconnected');
      setConnected(false);
      return false;
    }
  }, []);

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


      wsClient.current.on('calculation_completed', () => {
        setLoading(false);
      });

      wsClient.current.on('error', (data) => {
        setError(data.message || 'Erro desconhecido');
        setLoading(false);
      });

      wsClient.current.on('pong', () => {
        setLastPing(new Date());
      });

      // Conectar
      setConnectionStatus('connecting');
      wsClient.current.connect()
        .then(() => {
          setConnected(true);
          setConnectionStatus('connected');
          performHealthCheck();
        })
        .catch(() => {
          setConnected(false);
          setConnectionStatus('disconnected');
        });
    }

    return () => {
      if (wsClient.current) {
        wsClient.current.disconnect();
        wsClient.current = null;
      }
    };
  }, [performHealthCheck]);

  // Health check periódico
  useEffect(() => {
    const interval = setInterval(() => {
      if (connectionStatus === 'connected') {
        performHealthCheck();
      }
    }, 30000); // Check a cada 30 segundos

    // Check inicial
    performHealthCheck();

    return () => clearInterval(interval);
  }, [connectionStatus, performHealthCheck]);

  const lastCalculatedStateRef = useRef<string | null>(null);

  // Função para determinar o delay do debounce baseado no tipo de mudança
  const getDebounceDelay = useCallback((currentState: SimulatorState, previousState: SimulatorState | null) => {
    // Em testes E2E, usar delays muito mais baixos para acelerar
    const isTestEnvironment = typeof window !== 'undefined' && (
      window.location.hostname === 'localhost' &&
      (window.navigator.userAgent.includes('HeadlessChrome') || window.navigator.webdriver)
    );

    const baseDelay = isTestEnvironment ? 100 : 500; // 5x mais rápido em testes

    if (!previousState) return baseDelay;

    // Configurações técnicas que podem ter delay maior (não afetam cálculos imediatos)
    const technicalFields = [
      'mortality_table', 'calculation_method', 'payment_timing', 
      'salary_months_per_year', 'benefit_months_per_year'
    ];

    // Configurações que afetam cálculos e precisam de feedback mais rápido
    const immediateFields = [
      'age', 'salary', 'target_benefit', 'target_replacement_rate',
      'contribution_rate', 'accrual_rate', 'retirement_age', 'plan_type',
      'accumulation_rate', 'conversion_rate', 'discount_rate',
      'salary_growth_real'
    ];

    // Verificar quais campos mudaram
    const changedFields = Object.keys(currentState).filter(
      key => currentState[key as keyof SimulatorState] !== previousState[key as keyof SimulatorState]
    );

    // Se apenas campos técnicos mudaram, usar delay maior
    if (changedFields.length > 0 && changedFields.every(field => technicalFields.includes(field))) {
      return isTestEnvironment ? 150 : 1000; // Otimizado para testes
    }

    // Se campos de custo administrativo mudaram, delay médio
    if (changedFields.some(field => ['admin_fee_rate', 'loading_fee_rate'].includes(field))) {
      return isTestEnvironment ? 125 : 750; // Otimizado para testes
    }

    // Para outros campos, delay padrão
    return baseDelay;
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

  // Forçar reconexão
  const forceReconnect = useCallback(() => {
    if (wsClient.current) {
      wsClient.current.disconnect();
    }
    setConnectionStatus('connecting');

    setTimeout(() => {
      if (wsClient.current) {
        wsClient.current.connect()
          .then(() => {
            setConnected(true);
            setConnectionStatus('connected');
            performHealthCheck();
          })
          .catch(() => {
            setConnected(false);
            setConnectionStatus('disconnected');
          });
      }
    }, 100);
  }, [performHealthCheck]);

  return {
    // Estado
    state,
    results,
    loading,
    error,
    connected,

    // Status de conexão
    connectionStatus,
    lastPing,
    responseTime,

    // Dados auxiliares
    mortalityTables: mortalityTables || [],

    // Ações
    updateState,
    resetToDefault,
    recalculate,
    ping,
    forceReconnect,

    // Utilities
    isReady: !!state && !!mortalityTables,
  };
};