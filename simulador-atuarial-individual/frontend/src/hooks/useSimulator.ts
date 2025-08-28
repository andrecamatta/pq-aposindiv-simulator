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
      
      wsClient.current.on('sensitivity_update', (data) => {
        // Atualizar dados de sensibilidade se necessário
        console.log('Sensitivity data received:', data);
      });
      
      wsClient.current.on('calculation_completed', (data) => {
        setLoading(false);
        console.log(`Cálculo concluído em ${data.computation_time_ms}ms`);
      });
      
      wsClient.current.on('error', (data) => {
        setError(data.message || 'Erro desconhecido');
        setLoading(false);
      });
      
      wsClient.current.on('pong', (data) => {
        console.log('Pong received:', data);
      });
      
      // Conectar
      wsClient.current.connect()
        .then(() => setConnected(true))
        .catch((err) => {
          console.error('Falha na conexão WebSocket:', err);
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

  // Função debounced para cálculo
  const debouncedCalculate = useCallback((currentState: SimulatorState) => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
    }

    debounceTimeoutRef.current = setTimeout(() => {
      const preparedState = { ...currentState };
      
      if (preparedState.benefit_target_mode === 'REPLACEMENT_RATE') {
        // Quando o modo é taxa de reposição, limpamos o valor fixo para evitar ambiguidade.
        preparedState.target_benefit = undefined;
      } else {
        // Quando o modo é valor fixo, limpamos a taxa para evitar ambiguidade.
        preparedState.target_replacement_rate = undefined;
      }

      setLoading(true);
      apiService.calculate(preparedState)
        .then(setResults)
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }, 500); // Aumentado para 500ms para melhor UX em sliders/inputs
  }, []);

  // Inicializa o estado com os valores padrão da API.
  useEffect(() => {
    if (defaultState && !state) {
      setState(defaultState);
    }
  }, [defaultState, state]);

  // Efeito principal que reage a QUALQUER mudança no estado e dispara o cálculo.
  useEffect(() => {
    // Só executa se o estado já estiver inicializado.
    if (state) {
      debouncedCalculate(state);
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