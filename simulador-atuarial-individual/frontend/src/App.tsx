import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useSimulator } from './hooks/useSimulator';
import Sidebar from './components/Sidebar';
import ConfigurationSection from './components/sections/ConfigurationSection';
import CompactResultsSection from './components/sections/CompactResultsSection';
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
  const [activeSection, setActiveSection] = useState('dashboard');
  const {
    state,
    results,
    loading,
    error,
    connected,
    mortalityTables,
    updateState,
    resetToDefault,
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

  const renderSection = () => {
    switch (activeSection) {
      case 'dashboard':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full max-h-full">
            {/* Coluna de Configuração */}
            <div className="overflow-y-auto pr-2">
              {state && (
                <ConfigurationSection
                  state={state}
                  mortalityTables={mortalityTables}
                  onStateChange={updateState}
                  loading={loading}
                />
              )}
            </div>

            {/* Coluna de Resultados */}
            <div className="overflow-y-auto pr-2">
              <CompactResultsSection
                results={results}
                loading={loading}
              />
            </div>
          </div>
        );
      
      case 'reports':
        return (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-center text-gray-500 py-12">
              <h3 className="text-lg font-medium">📄 Relatórios</h3>
              <p className="mt-2">Funcionalidade em desenvolvimento</p>
              <p className="text-sm">Exportação de PDF, Excel e relatórios técnicos</p>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="h-screen bg-gray-50 flex overflow-hidden">
      {/* Sidebar */}
      <Sidebar 
        activeSection={activeSection}
        onSectionChange={setActiveSection}
        connected={connected}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  {activeSection === 'dashboard' && '📊 Simulador Atuarial Individual'}
                  {activeSection === 'reports' && '📄 Relatórios e Exportação'}
                </h1>
                <p className="text-sm text-gray-500">
                  {activeSection === 'dashboard' && 'Configure os parâmetros e visualize os resultados em tempo real'}
                  {activeSection === 'reports' && 'Gerar documentos e exportações'}
                </p>
              </div>
              
              {loading && (
                <div className="flex items-center space-x-2 text-blue-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span className="text-sm">Calculando...</span>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Botão Reset */}
              <button
                onClick={resetToDefault}
                className="px-4 py-2 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors shadow-sm flex items-center space-x-2"
                disabled={loading}
              >
                <span>🔄</span>
                <span>Resetar</span>
              </button>
            </div>
          </div>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-400 p-4 mx-6 mt-4 rounded-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <span className="text-red-400 text-lg">⚠️</span>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700 font-medium">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <main className="flex-1 p-4 overflow-hidden">
          {renderSection()}
        </main>
      </div>
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
