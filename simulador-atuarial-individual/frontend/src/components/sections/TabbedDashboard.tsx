import React, { useState } from 'react';
import type { SimulatorState, SimulatorResults, MortalityTable } from '../../types';
import { TabNavigation, tabs, type Tab } from '../../design-system/components';
import ParticipantTab from '../tabs/ParticipantTab';
import AssumptionsTab from '../tabs/AssumptionsTab';
import ResultsTab from '../tabs/ResultsTab';
import SensitivityTab from '../tabs/SensitivityTab';
import TechnicalTab from '../tabs/TechnicalTab';
import ReportsTab from '../tabs/ReportsTab';
import SmartSuggestions from '../cards/SmartSuggestions';
import { formatCurrencyBR, formatSliderDisplayBR, formatSimplePercentageBR } from '../../utils/formatBR';

interface TabbedDashboardProps {
  state: SimulatorState;
  results: SimulatorResults | null;
  mortalityTables: MortalityTable[];
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const TabbedDashboard: React.FC<TabbedDashboardProps> = ({
  state,
  results,
  mortalityTables,
  onStateChange,
  loading
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
      case 'sensitivity':
        return (
          <SensitivityTab
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
        return (
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-4">Análise Rápida</h3>
            {results ? (
              <div className="space-y-4 text-sm text-gray-700">
                <div>
                  {state.plan_type === 'CD' ? (
                    <>
                      <h4 className="text-xs font-semibold uppercase tracking-wide mb-2">Saldo & Rendimento</h4>
                      <div className="space-y-1">
                        <p>Saldo Acumulado: {formatCurrencyBR(results.individual_balance || 0)}</p>
                        <p>Rendimento Total: {formatCurrencyBR(results.accumulated_return || 0)}</p>
                        <p>Renda Mensal CD: {formatCurrencyBR(results.monthly_income_cd || 0)}</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <h4 className="text-xs font-semibold uppercase tracking-wide mb-2">Reservas Técnicas</h4>
                      <div className="space-y-1">
                        <p>RMBA: {formatCurrencyBR(results.rmba)}</p>
                        <p>RMBC: {formatCurrencyBR(results.rmbc)}</p>
                        <p className={`font-medium ${results.deficit_surplus >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                          {results.deficit_surplus >= 0 ? 'Superávit' : 'Déficit'}: {formatCurrencyBR(Math.abs(results.deficit_surplus))}
                        </p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-600">Configure os parâmetros para ver os resultados.</p>
            )}
          </div>
        );
      case 'sensitivity':
        return (
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-4">Análise de Sensibilidade</h3>
            {results ? (
              <div className="space-y-4 text-sm text-gray-700">
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wide mb-2">Sobre a Análise</h4>
                  <div className="space-y-2">
                    <p>A análise de sensibilidade mostra como mudanças nas premissas atuariais impactam as métricas principais.</p>
                    <p>Gráficos tornado facilitam a identificação dos fatores de maior impacto no resultado.</p>
                  </div>
                </div>
                
                {state.plan_type === 'BD' && (
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wide mb-2">Plano BD - RMBA</h4>
                    <div className="space-y-1">
                      <p>• <span className="font-medium text-red-600">Vermelho:</span> Aumenta RMBA (piora equilíbrio)</p>
                      <p>• <span className="font-medium text-green-600">Verde:</span> Reduz RMBA (melhora equilíbrio)</p>
                    </div>
                  </div>
                )}

                {state.plan_type === 'CD' && (
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wide mb-2">Plano CD - Renda</h4>
                    <div className="space-y-1">
                      <p>• <span className="font-medium text-green-600">Verde:</span> Aumenta renda mensal</p>
                      <p>• <span className="font-medium text-red-600">Vermelho:</span> Reduz renda mensal</p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-600">Execute a simulação para ver a análise de sensibilidade.</p>
            )}
          </div>
        );
      case 'technical':
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
      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 bg-white p-8 rounded-lg shadow-md">
            {renderTabContent()}
          </div>
          <div className="bg-white p-8 rounded-lg shadow-md h-fit">
            {renderSidebar()}
          </div>
        </div>
      </main>
    </div>
  );
};

export default TabbedDashboard;
