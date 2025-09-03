import React, { useState } from 'react';
import type { SimulatorState, SimulatorResults, MortalityTable } from '../../types';
import { TabNavigation, tabs, type Tab } from '../../design-system/components';
import ParticipantTab from '../tabs/ParticipantTab';
import AssumptionsTab from '../tabs/AssumptionsTab';
import ResultsTab from '../tabs/ResultsTab';
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
  const [activeTab, setActiveTab] = useState('technical');
  
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
        return (
          <>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">
                Dados do Participante
              </h3>
              <div className="space-y-3 text-sm text-gray-600">
                <p className="font-medium">Idade: {state.age || '—'} anos</p>
                <p>Gênero: {state.gender === 'M' ? 'Masculino' : state.gender === 'F' ? 'Feminino' : '—'}</p>
                <p>Salário: {state.salary ? formatCurrencyBR(state.salary, 2) : '—'}</p>
                <p>Saldo Inicial: {state.initial_balance ? formatCurrencyBR(state.initial_balance, 2) : '—'}</p>
              </div>
            </div>

          </>
        );
      case 'assumptions':
        return (
          <>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">
                Resumo das Premissas
              </h3>
              <div className="space-y-3 text-sm text-gray-600">
                <p>Benefício: {formatCurrencyBR(state.target_benefit || 0, 2)}</p>
                <p>Contribuição: {formatSimplePercentageBR(state.contribution_rate || 0, 2)}</p>
                <p>Rentabilidade: {formatSimplePercentageBR(state.accrual_rate || 5, 2)} a.a.</p>
                <p className="text-xs text-gray-500 mt-4">
                  Ajuste os valores para ver o impacto nos resultados em tempo real.
                </p>
              </div>
            </div>


            {/* Sugestões Inteligentes */}
            <SmartSuggestions 
              state={state}
              onStateChange={onStateChange}
              loading={loading}
            />
          </>
        );
      case 'results':
        return (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span>Análise Rápida</span>
            </h3>
            {results ? (
              <div className="space-y-4 text-sm text-gray-600">
                {/* Métricas Financeiras - Condicionais por Tipo de Plano */}
                <div>
                  {state.plan_type === 'CD' ? (
                    <>
                      <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Saldo & Rendimento</h4>
                      <div className="space-y-1">
                        <p>Saldo Acumulado: {formatCurrencyBR(results.individual_balance || 0)}</p>
                        <p>Rendimento Total: {formatCurrencyBR(results.accumulated_return || 0)}</p>
                        <p>Renda Mensal CD: {formatCurrencyBR(results.monthly_income_cd || 0)}</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Reservas Técnicas</h4>
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

                {/* Métricas Condicionais por Tipo de Plano */}
                <div>
                  {state.plan_type === 'CD' ? (
                    <>
                      <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Resumo CD</h4>
                      <div className="space-y-1">
                        <p>Tempo Acumulação: {Math.round(((state.retirement_age || 65) - (state.age || 30)))} anos</p>
                        <p>Tempo Benefícios: {(() => {
                          // Usar duração calculada precisamente no backend
                          if (results.benefit_duration_years !== undefined && results.benefit_duration_years !== null) {
                            if (results.benefit_duration_years === Infinity || results.benefit_duration_years > 50) {
                              return 'Vitalício';
                            }
                            return `${Math.round(results.benefit_duration_years)} anos`;
                          }
                          
                          // Fallback para modalidades com prazo determinado (caso backend não tenha calculado)
                          const conversionModeYears: Record<string, number> = {
                            'CERTAIN_5Y': 5,
                            'CERTAIN_10Y': 10,
                            'CERTAIN_15Y': 15,
                            'CERTAIN_20Y': 20
                          };
                          
                          if (state.cd_conversion_mode && conversionModeYears[state.cd_conversion_mode]) {
                            return `${conversionModeYears[state.cd_conversion_mode]} anos`;
                          }
                          
                          return '—';
                        })()}</p>
                        <p>Modalidade: {state.cd_conversion_mode === 'ACTUARIAL' ? 'Vitalícia' : 
                          state.cd_conversion_mode === 'CERTAIN_20Y' ? '20 anos' :
                          state.cd_conversion_mode === 'CERTAIN_15Y' ? '15 anos' :
                          state.cd_conversion_mode === 'CERTAIN_10Y' ? '10 anos' :
                          state.cd_conversion_mode === 'CERTAIN_5Y' ? '5 anos' : 'Vitalícia'}</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Taxas de Reposição</h4>
                      <div className="space-y-1">
                        <p>Taxa Alvo: {formatSimplePercentageBR(results.target_replacement_ratio || 0, 2)}</p>
                        <p>Taxa Sustentável: {formatSimplePercentageBR(results.sustainable_replacement_ratio || 0, 2)}</p>
                      </div>
                    </>
                  )}
                </div>

                {/* Parâmetros Atuais - Condicionais por Tipo de Plano */}
                <div>
                  <h4 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">Parâmetros</h4>
                  <div className="space-y-1">
                    <p>Benefício: {state.benefit_target_mode === 'VALUE'
                        ? formatCurrencyBR(state.target_benefit || 0, 2)
                        : formatSimplePercentageBR(state.target_replacement_rate || 70, 2)
                      }</p>
                    <p>Contribuição: {formatSimplePercentageBR(state.contribution_rate || 0, 2)}</p>
                    {state.plan_type === 'CD' ? (
                      <>
                        <p>Taxa Acumulação: {formatSimplePercentageBR((state.accumulation_rate || 0.065) * 100, 2)} a.a.</p>
                        <p>Taxa Conversão: {formatSimplePercentageBR((state.conversion_rate || 0.045) * 100, 2)} a.a.</p>
                      </>
                    ) : (
                      <p>Rentabilidade: {formatSimplePercentageBR(state.accrual_rate || 5, 2)} a.a.</p>
                    )}
                  </div>
                </div>

                <p className="text-xs text-gray-500 flex items-center gap-2 mt-4">
                  <span>Simulação atualizada com os parâmetros atuais.</span>
                </p>
              </div>
            ) : (
              <p className="text-sm text-gray-600">Configure os parâmetros para ver os resultados.</p>
            )}
          </div>
        );
      case 'technical':
        return (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span>Base Técnica</span>
            </h3>
            <div className="space-y-3 text-sm text-gray-600">
              <p>Tábua: {state.mortality_table || 'BR_EMS_2021'}</p>
              <p>Método: {state.calculation_method || 'PUC'}</p>
              <p className="text-xs text-gray-500 flex items-center gap-2 mt-4">
                    <span>Configurações utilizadas nos cálculos atuariais.</span>
              </p>
            </div>
          </div>
        );
      default:
        return (
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="font-semibold text-gray-900 mb-4">
              Relatórios
            </h3>
            <div className="space-y-3 text-sm text-gray-600">
              <p>Gere documentos profissionais com os resultados da simulação.</p>
              <p className="text-xs text-gray-500">Formatos disponíveis: PDF, Excel, Word</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header Global with integrated tabs */}
      <TabNavigation 
        activeTab={activeTab}
        onTabChange={setActiveTab}
        state={state}
        results={results}
      />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-8 py-8">
        <div className="grid grid-cols-12 gap-12">
          {/* Main Content Column */}
          <div className="col-span-8">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 min-h-[600px]">
              <div className="p-8">
                {renderTabContent()}
              </div>
            </div>
          </div>

          {/* Sidebar Column */}
          <div className="col-span-4 space-y-6">
            {renderSidebar()}
            
            {/* Loading State */}
            {loading && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center space-x-3">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#13a4ec]"></div>
                  <span className="text-sm font-medium text-gray-700">Calculando simulação...</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TabbedDashboard;
