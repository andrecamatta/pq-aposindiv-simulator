import React from 'react';
import { TrendingUp, DollarSign, AlertTriangle, CheckCircle, BarChart3, PieChart } from 'lucide-react';
import type { SimulatorResults, SimulatorState } from '../../types';
import { formatCurrency, formatPercentage } from '../../utils/formatting';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent
} from '../../design-system/components';
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
      <div className="space-y-6">
        {/* Loading Hero */}
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="p-8">
            <div className="flex items-center justify-center min-h-[200px]">
              <div className="text-center">
                <div className="w-16 h-16 bg-white rounded-2xl shadow-lg flex items-center justify-center mx-auto mb-4">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
                </div>
                <h2 className="text-xl font-bold text-green-900 mb-2">Calculando Resultados</h2>
                <p className="text-green-600">Processando as premissas atuariais...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="space-y-6">
        {/* Empty State */}
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="p-8">
            <div className="text-center min-h-[200px] flex items-center justify-center">
              <div>
                <div className="w-16 h-16 bg-white rounded-2xl shadow-lg flex items-center justify-center mx-auto mb-4">
                  <BarChart3 className="w-8 h-8 text-green-500" />
                </div>
                <h2 className="text-xl font-bold text-green-900 mb-2">Aguardando Dados</h2>
                <p className="text-green-600">Configure os parâmetros nas abas anteriores para ver os resultados</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const superavitStatus = getSuperavitStatus(results.deficit_surplus);
  const StatusIcon = superavitStatus.icon;

  return (
    <div className="space-y-6">



      {/* Visualizações Gráficas */}
      <div className="grid grid-cols-1 gap-6">
        {/* Composição da RMBA */}
        <Card className="bg-white border-green-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <PieChart className="w-5 h-5 text-purple-600" />
              </div>
              Composição da RMBA
            </CardTitle>
          </CardHeader>
          <CardContent>
            <VPABarChart results={results} />
          </CardContent>
        </Card>

        {/* Análise de Suficiência Financeira */}
        <Card className="bg-white border-green-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-blue-600" />
              </div>
              Análise de Suficiência Financeira
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SufficiencyAnalysisChart results={results} state={state} />
          </CardContent>
        </Card>
      </div>

      {/* Dois Gráficos de Análise Temporal */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Simulação Determinística */}
        <Card className="bg-white border-blue-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-blue-600" />
              </div>
              Simulação Realística
            </CardTitle>
          </CardHeader>
          <CardContent>
            <DeterministicChart results={results} currentAge={state.age} />
          </CardContent>
        </Card>

        {/* Análise Atuarial */}
        <Card className="bg-white border-purple-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <PieChart className="w-5 h-5 text-purple-600" />
              </div>
              Análise Atuarial
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ActuarialChart results={results} currentAge={state.age} />
          </CardContent>
        </Card>
      </div>

      {/* Interpretation Guide */}
      <Card className="bg-white border-green-200">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <span className="text-2xl">📊</span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Interpretação dos Resultados</h3>
              <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600">
                <div>
                  <p className="mb-2"><strong>RMBA:</strong> Valor presente das obrigações futuras com participantes ativos.</p>
                  <p className="mb-2"><strong>RMBC:</strong> Valor das obrigações com participantes já aposentados.</p>
                  <p className="mb-2"><strong>Taxa de Reposição Alvo:</strong> Percentual que o benefício desejado representa do salário final.</p>
                </div>
                <div>
                  {/* Changed from > to literal > and < to literal < */}
                  <p className="mb-2"><strong>Taxa de Reposição Sustentável:</strong> Percentual que o benefício calculado representa do salário final, considerando as contribuições.</p>
                  <p className="mb-2"><strong>Superávit {'>'} 0:</strong> Reservas suficientes para cobrir as obrigações.</p>
                  <p className="mb-2"><strong>Superávit {'<'} 0:</strong> Déficit que requer aportes adicionais.</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResultsTab;
