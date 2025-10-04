import React, { useState } from 'react';
import type { SimulatorState, SimulatorResults, MortalityTable } from '../../types';
import { TabNavigation, tabs, type Tab } from '../../design-system/components';
import ParticipantTab from '../tabs/ParticipantTab';
import AssumptionsTab from '../tabs/AssumptionsTab';
import ResultsTab from '../tabs/ResultsTab';
import TechnicalTab from '../tabs/TechnicalTab';
import TablesAnalysisTab from '../tabs/TablesAnalysisTab';
import ReportsTab from '../tabs/ReportsTab';
import SmartSuggestions from '../cards/SmartSuggestions';
import { formatCurrencyBR, formatSliderDisplayBR, formatSimplePercentageBR } from '../../utils/formatBR';

interface TabbedDashboardProps {
  state: SimulatorState;
  results: SimulatorResults | null;
  mortalityTables: MortalityTable[];
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
  connectionStatus?: 'connected' | 'disconnected' | 'connecting';
  lastPing?: Date;
  responseTime?: number;
  onReconnect?: () => void;
}

const TabbedDashboard: React.FC<TabbedDashboardProps> = ({
  state,
  results,
  mortalityTables,
  onStateChange,
  loading,
  connectionStatus,
  lastPing,
  responseTime,
  onReconnect
}) => {
  const [activeTab, setActiveTab] = useState('participant');

  const currentTab = tabs.find(tab => tab.id === activeTab);
  
  const renderTabContent = () => {
    switch (activeTab) {
      case 'participant':
        return (
          <ParticipantTab
            state={state}
            onStateChange={onStateChange}
            loading={loading}
          />
        );
      case 'assumptions':
        return (
          <AssumptionsTab
            state={state}
            onStateChange={onStateChange}
            loading={loading}
          />
        );
      case 'results':
        return (
          <ResultsTab
            results={results}
            state={state}
            loading={loading}
          />
        );
      case 'technical':
        return (
          <TechnicalTab
            state={state}
            mortalityTables={mortalityTables}
            onStateChange={onStateChange}
            loading={loading}
          />
        );
      case 'tables':
        return (
          <TablesAnalysisTab
            mortalityTables={mortalityTables}
            loading={loading}
          />
        );
      case 'reports':
        return (
          <ReportsTab
            results={results}
            state={state}
            loading={loading}
          />
        );
      default:
        return null;
    }
  };

  const renderSidebar = () => {
    if (!currentTab) return null;
    
    // Content contextual à aba ativa com cores modernas
    switch (activeTab) {
      case 'participant':
        return null;
      case 'assumptions':
        return (
          <SmartSuggestions 
            state={state}
            onStateChange={onStateChange}
            loading={loading}
          />
        );
      case 'results':
        return null;
      case 'technical':
        return null;
      case 'tables':
        return null;
      default:
        return (
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-4">Relatórios</h3>
            <div className="space-y-3 text-gray-700">
              <p>Gere documentos profissionais com os resultados da simulação.</p>
              <p className="text-xs text-gray-500">Formatos disponíveis: PDF, Excel, Word</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <TabNavigation
        activeTab={activeTab}
        onTabChange={setActiveTab}
        connectionStatus={connectionStatus}
        lastPing={lastPing}
        responseTime={responseTime}
        onReconnect={onReconnect}
      />
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className={`bg-white p-8 rounded-lg shadow-md ${activeTab === 'results' || activeTab === 'tables' ? 'lg:col-span-3' : 'lg:col-span-2'}`}>
            {renderTabContent()}
          </div>
          {activeTab !== 'results' && activeTab !== 'tables' && (
            <div className="bg-white p-8 rounded-lg shadow-md h-fit">
              {renderSidebar()}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default TabbedDashboard;
