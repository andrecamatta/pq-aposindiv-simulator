import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSimulator } from './hooks/useSimulator';
import TabbedDashboard from './components/sections/TabbedDashboard';
import { ToastProvider } from './design-system/components';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

const SimulatorApp: React.FC = () => {
  const {
    state,
    results,
    loading,
    error,
    connectionStatus,
    lastPing,
    responseTime,
    mortalityTables,
    updateState,
    resetToDefault,
    forceReconnect,
    isReady,
  } = useSimulator();

  if (!isReady) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando simulador atuarial...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md text-center">
          <div className="text-red-400 text-4xl mb-4">⚠️</div>
          <h2 className="text-lg font-medium text-red-800 mb-2">Erro no Simulador</h2>
          <p className="text-sm text-red-700 mb-4">{error}</p>
          <button
            onClick={resetToDefault}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Reiniciar Simulador
          </button>
        </div>
      </div>
    );
  }

  if (!state) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-pulse text-4xl mb-4">⚙️</div>
          <p className="text-gray-600">Inicializando estado do simulador...</p>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="simulator-ready">
      <TabbedDashboard
        state={state}
        results={results}
        mortalityTables={mortalityTables}
        onStateChange={updateState}
        loading={loading}
        connectionStatus={connectionStatus}
        lastPing={lastPing}
        responseTime={responseTime}
        onReconnect={forceReconnect}
      />
    </div>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider maxToasts={5}>
        <SimulatorApp />
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;
