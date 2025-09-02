import React from 'react';
import { TrendingUp, DollarSign, AlertTriangle, CheckCircle, BarChart3, PieChart } from 'lucide-react';
import type { SimulatorResults, SimulatorState } from '../../types';
import { formatCurrencyBR, formatPercentageBR } from '../../utils/formatBR';
import { DeterministicChart, ActuarialChart, VPABarChart, SufficiencyBarChart, SufficiencyAnalysisChart } from '../charts';

interface ResultsTabProps {
  results: SimulatorResults | null;
  state: SimulatorState;
  loading: boolean;
}

const ResultsTab: React.FC<ResultsTabProps> = ({ results, state, loading }) => {

  const getSuperavitStatus = (superavit: number) => {
    if (superavit > 0) return { color: 'emerald', icon: CheckCircle, text: 'Superávit', bg: 'from-emerald-100 to-green-100' };
    if (superavit === 0) return { color: 'yellow', icon: AlertTriangle, text: 'Equilibrado', bg: 'from-yellow-100 to-amber-100' };
    return { color: 'red', icon: AlertTriangle, text: 'Déficit', bg: 'from-red-100 to-rose-100' };
  };

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3 mb-2">
            <TrendingUp className="w-6 h-6 text-emerald-600" />
            Resultados da Simulação
          </h1>
          <p className="text-gray-600">Análise completa das projeções atuariais e financeiras.</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="flex items-center justify-center min-h-[200px]">
            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Calculando Resultados</h2>
              <p className="text-gray-600">Processando as premissas atuariais...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="space-y-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3 mb-2">
            <TrendingUp className="w-6 h-6 text-emerald-600" />
            Resultados da Simulação
          </h1>
          <p className="text-gray-600">Análise completa das projeções atuariais e financeiras.</p>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="text-center min-h-[200px] flex items-center justify-center">
            <div>
              <div className="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-emerald-500" />
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Aguardando Dados</h2>
              <p className="text-gray-600">Configure os parâmetros nas abas anteriores para ver os resultados</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const superavitStatus = getSuperavitStatus(results.deficit_surplus);
  const StatusIcon = superavitStatus.icon;

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3 mb-2">
          <TrendingUp className="w-6 h-6 text-emerald-600" />
          Resultados da Simulação
        </h1>
        <p className="text-gray-600">Análise completa das projeções atuariais e financeiras.</p>
      </div>

      {/* Visualizações Gráficas */}
      <div className="grid grid-cols-1 gap-8">
        {/* Análise de Suficiência Financeira */}
        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-blue-600" />
              </div>
              Análise de Suficiência Financeira
            </h2>
          </div>
          <SufficiencyAnalysisChart results={results} state={state} />
        </div>

        {/* Composição da RMBA */}
        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                <PieChart className="w-5 h-5 text-purple-600" />
              </div>
              Composição da RMBA
            </h2>
          </div>
          <VPABarChart results={results} />
        </div>
      </div>

      {/* Dois Gráficos de Análise Temporal */}
      <div className="grid lg:grid-cols-2 gap-8">
        {/* Simulação Determinística */}
        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-blue-600" />
              </div>
              Simulação Realística
            </h2>
          </div>
          <DeterministicChart results={results} currentAge={state.age} />
        </div>

        {/* Análise Atuarial */}
        <div className="bg-white rounded-xl shadow-sm p-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center">
                <PieChart className="w-5 h-5 text-purple-600" />
              </div>
              Análise Atuarial
            </h2>
          </div>
          <ActuarialChart results={results} currentAge={state.age} />
        </div>
      </div>

      {/* Interpretation Guide */}
      <div className="bg-white rounded-xl shadow-sm p-8">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center flex-shrink-0">
            <span className="text-2xl">📊</span>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Interpretação dos Resultados</h3>
            <div className="grid md:grid-cols-2 gap-6 text-sm text-gray-600">
              <div className="space-y-3">
                <p><strong>RMBA:</strong> Valor presente das obrigações futuras com participantes ativos.</p>
                <p><strong>RMBC:</strong> Valor das obrigações com participantes já aposentados.</p>
                <p><strong>Taxa de Reposição Alvo:</strong> Percentual que o benefício desejado representa do salário final.</p>
              </div>
              <div className="space-y-3">
                <p><strong>Taxa de Reposição Sustentável:</strong> Percentual que o benefício calculado representa do salário final, considerando as contribuições.</p>
                <p><strong>Superávit {'>'} 0:</strong> Reservas suficientes para cobrir as obrigações.</p>
                <p><strong>Superávit {'<'} 0:</strong> Déficit que requer aportes adicionais.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsTab;
