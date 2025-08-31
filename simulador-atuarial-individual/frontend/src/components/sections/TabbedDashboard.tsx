import React, { useState } from 'react';
import type { SimulatorState, SimulatorResults, MortalityTable } from '../../types';
import { TabNavigation, tabs, type Tab } from '../../design-system/components';
import ParticipantTab from '../tabs/ParticipantTab';
import AssumptionsTab from '../tabs/AssumptionsTab';
import ResultsTab from '../tabs/ResultsTab';
import TechnicalTab from '../tabs/TechnicalTab';
import ReportsTab from '../tabs/ReportsTab';

const formatSalary = (salary: number) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: 0
  }).format(salary);
};

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
            <div className="bg-gradient-to-br from-blue-50 to-blue-100/80 rounded-xl shadow-card p-6 border border-blue-200/30 backdrop-blur-sm">
              <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">📋 <span>Dados do Participante</span></h3>
              <div className="space-y-3 text-sm text-blue-800">
                <div className="bg-white/70 rounded-lg p-3 backdrop-blur-sm">
                  <p className="font-medium">Idade: {state.age || '—'} anos</p>
                  <p>Gênero: {state.gender === 'M' ? 'Masculino' : state.gender === 'F' ? 'Feminino' : '—'}</p>
                  <p>Salário: {state.salary ? formatSalary(state.salary) : '—'}</p>
                  <p>Saldo Inicial: {state.initial_balance ? formatSalary(state.initial_balance) : '—'}</p>
                </div>
              </div>
            </div>


            {/* Help Card */}
            <div className="bg-white border-blue-200/50 rounded-xl p-6">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-lg">💡</span>
                </div>
                <div>
                  <h3 className="text-base font-semibold text-gray-900 mb-2">Orientações</h3>
                  <div className="space-y-2 text-xs text-gray-600">
                    <p><strong>Idade:</strong> Utilize a idade atual em anos completos.</p>
                    <p><strong>Gênero:</strong> Necessário para a tábua de mortalidade.</p>
                    <p><strong>Salário:</strong> Informe o valor bruto mensal atual.</p>
                  </div>
                </div>
              </div>
            </div>
          </>
        );
      case 'assumptions':
        return (
          <>
            <div className="bg-gradient-to-br from-violet-50 to-violet-100/80 rounded-xl shadow-card p-6 border border-violet-200/30 backdrop-blur-sm">
              <h3 className="font-semibold text-violet-900 mb-3 flex items-center gap-2">⚙️ <span>Resumo das Premissas</span></h3>
              <div className="space-y-3 text-sm text-violet-800">
                <div className="bg-white/70 rounded-lg p-3 space-y-2 backdrop-blur-sm">
                  <p>Benefício: R$ {((state.target_benefit || 0)/1000).toFixed(1)}k</p>
                  <p>Contribuição: {state.contribution_rate || 0}%</p>
                  <p>Rentabilidade: {state.accrual_rate || 5}% a.a.</p>
                </div>
                <p className="text-xs text-violet-700">
                  📊 Ajuste os valores para ver o impacto nos resultados em tempo real.
                </p>
              </div>
            </div>

            {/* Help Card */}
            <div className="bg-white border-purple-200/50 rounded-xl p-6">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-xl">📊</span>
                </div>
                <div>
                  <h3 className="text-base font-semibold text-gray-900 mb-2">Orientações Técnicas</h3>
                  <div className="space-y-2 text-xs text-gray-600">
                    <p><strong>Taxa de Acumulação:</strong> Rentabilidade durante a acumulação.</p>
                    <p><strong>Taxa de Desconto:</strong> Taxa para cálculo do valor presente.</p>
                    <p><strong>Crescimento Salarial:</strong> Projeção de evolução real.</p>
                  </div>
                </div>
              </div>
            </div>
          </>
        );
      case 'results':
        return (
          <div className="bg-gradient-to-br from-emerald-50 to-emerald-100/80 rounded-xl shadow-card p-6 border border-emerald-200/30 backdrop-blur-sm">
            <h3 className="font-semibold text-emerald-900 mb-3 flex items-center gap-2">📈 <span>Análise Rápida</span></h3>
            {results ? (
              <div className="space-y-3 text-sm text-emerald-800">
                {/* Reservas Técnicas */}
                <div className="bg-white/70 rounded-lg p-3 backdrop-blur-sm">
                  <h4 className="text-xs font-semibold text-emerald-700 uppercase tracking-wide mb-2">Reservas Técnicas</h4>
                  <div className="space-y-1">
                    <p>RMBA: R$ {results.rmba.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                    <p>RMBC: R$ {results.rmbc.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                    <p className={`font-medium ${results.deficit_surplus >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>
                      {results.deficit_surplus >= 0 ? 'Superávit' : 'Déficit'}: R$ {Math.abs(results.deficit_surplus).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>

                {/* Taxas de Reposição */}
                <div className="bg-white/70 rounded-lg p-3 backdrop-blur-sm">
                  <h4 className="text-xs font-semibold text-emerald-700 uppercase tracking-wide mb-2">Taxas de Reposição</h4>
                  <div className="space-y-1">
                    <p>Taxa Alvo: {(results.target_replacement_ratio || 0).toFixed(1)}%</p>
                    <p>Taxa Sustentável: {(results.sustainable_replacement_ratio || 0).toFixed(1)}%</p>
                  </div>
                </div>

                {/* Parâmetros Atuais */}
                <div className="bg-white/70 rounded-lg p-3 backdrop-blur-sm">
                  <h4 className="text-xs font-semibold text-emerald-700 uppercase tracking-wide mb-2">Parâmetros</h4>
                  <div className="space-y-1">
                    <p>Benefício: {state.benefit_target_mode === 'VALUE'
                        ? `R$ ${(state.target_benefit || 0).toLocaleString('pt-BR')}`
                        : `${state.target_replacement_rate || 70}%`
                      }</p>
                    <p>Contribuição: {state.contribution_rate || 0}%</p>
                    <p>Rentabilidade: {state.accrual_rate || 5}% a.a.</p>
                  </div>
                </div>

                <p className="text-xs text-emerald-700">
                  ✅ Simulação atualizada com os parâmetros atuais.
                </p>
              </div>
            ) : (
              <p className="text-sm text-emerald-700">Configure os parâmetros para ver os resultados.</p>
            )}
          </div>
        );
      case 'technical':
        return (
          <div className="bg-gradient-to-br from-orange-50 to-orange-100/80 rounded-xl shadow-card p-6 border border-orange-200/30 backdrop-blur-sm">
            <h3 className="font-semibold text-orange-900 mb-3 flex items-center gap-2">🔧 <span>Base Técnica</span></h3>
            <div className="space-y-3 text-sm text-orange-800">
              <div className="bg-white/70 rounded-lg p-3 space-y-1 backdrop-blur-sm">
                <p>Tábua: {state.mortality_table || 'BR_EMS_2021'}</p>
                <p>Método: {state.calculation_method || 'PUC'}</p>
              </div>
              <p className="text-xs text-orange-700">
                ⚙️ Configurações utilizadas nos cálculos atuariais.
              </p>
            </div>
          </div>
        );
      default:
        return (
          <div className="bg-gradient-to-br from-pink-50 to-pink-100/80 rounded-xl shadow-card p-6 border border-pink-200/30 backdrop-blur-sm">
            <h3 className="font-semibold text-pink-900 mb-3 flex items-center gap-2">📋 <span>Relatórios</span></h3>
            <div className="space-y-3 text-sm text-pink-800">
              <p>Gere documentos profissionais com os resultados da simulação.</p>
              <div className="bg-white/70 rounded-lg p-3 backdrop-blur-sm">
                <p className="text-xs">Formatos disponíveis: PDF, Excel, Word</p>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div 
      className="min-h-screen transition-colors duration-300"
      style={{
        background: currentTab ? `linear-gradient(135deg, ${currentTab.color.light}08, ${currentTab.color.primary}03)` : '#f8fafc'
      }}
    >
      {/* Tab Navigation */}
      <TabNavigation
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Main Content - 3 Column Layout */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-12 gap-6">
          {/* Main Content Column */}
          <div className="col-span-8">
            <div className="min-h-[600px]">
              {renderTabContent()}
            </div>
          </div>

          {/* Sidebar Column */}
          <div className="col-span-4 space-y-6">
            {renderSidebar()}
            
      {/* Loading State */}
      {loading && (
        <div className="bg-gradient-to-br from-gray-50 to-gray-100/80 rounded-xl shadow-card p-6 border border-gray-200/30 backdrop-blur-sm">
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="text-sm font-medium text-gray-800">Calculando simulação...</span>
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
