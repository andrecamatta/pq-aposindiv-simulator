import React from 'react';
import { TrendingUp, DollarSign, AlertTriangle, CheckCircle } from 'lucide-react';
import type { SimulatorResults } from '../../types';
import { formatCurrency } from '../../utils';
import { Card, CardHeader, CardTitle, CardContent } from '../../design-system/components';

interface ResultsCardProps {
  results: SimulatorResults | null;
  loading: boolean;
}

const ResultsCard: React.FC<ResultsCardProps> = ({ results, loading }) => {

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const getSuperavitStatus = (superavit: number) => {
    if (superavit > 3.0) return { color: 'success', icon: CheckCircle, text: 'Excelente' };
    if (superavit > 2.0) return { color: 'success', icon: CheckCircle, text: 'Bom' };
    if (superavit > 1.0) return { color: 'warning', icon: AlertTriangle, text: 'Adequado' };
    return { color: 'error', icon: AlertTriangle, text: 'Insuficiente' };
  };

  if (loading) {
    return (
      <Card variant="default" padding="lg" className="h-full">
        <CardHeader>
          <CardTitle>Resultados</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Skeleton for main values */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="h-8 bg-gray-200 rounded"></div>
              </div>
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded mb-2"></div>
                <div className="h-8 bg-gray-200 rounded"></div>
              </div>
            </div>
            
            {/* Skeleton for superavit */}
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 rounded mb-2"></div>
              <div className="h-12 bg-gray-200 rounded"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!results) {
    return (
      <Card variant="default" padding="lg" className="h-full">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500">
            <TrendingUp className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium mb-2">Aguardando Cálculos</h3>
            <p className="text-sm">Configure os parâmetros para ver os resultados</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const superavitStatus = getSuperavitStatus(results.deficit_surplus_percentage);
  const StatusIcon = superavitStatus.icon;

  return (
    <Card variant="default" padding="lg" className="h-full">
      <CardHeader withBorder>
        <CardTitle className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-primary-600" />
          </div>
          Resultados da Simulação
        </CardTitle>
      </CardHeader>
      
      <CardContent className="pt-6">
        <div className="space-y-8">
          {/* Main Values Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* RMBA */}
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-blue-700">RMBA</span>
                <DollarSign className="w-4 h-4 text-blue-600" />
              </div>
              <div className="text-2xl font-bold text-blue-900">
                {formatCurrency(results.rmba)}
              </div>
              <p className="text-xs text-blue-600 mt-1">Reserva Matemática de Benefícios a Conceder</p>
            </div>

            {/* RMBC */}
            <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-green-700">RMBC</span>
                <DollarSign className="w-4 h-4 text-green-600" />
              </div>
              <div className="text-2xl font-bold text-green-900">
                {formatCurrency(results.rmbc)}
              </div>
              <p className="text-xs text-green-600 mt-1">Reserva Matemática de Benefícios Concedidos</p>
            </div>
          </div>

          {/* Superavit Highlight */}
          <div className={`bg-gradient-to-r ${
            superavitStatus.color === 'success' ? 'from-green-50 to-emerald-50 border-green-200' :
            superavitStatus.color === 'warning' ? 'from-yellow-50 to-orange-50 border-yellow-200' :
            'from-red-50 to-pink-50 border-red-200'
          } rounded-xl p-6 border-2`}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  superavitStatus.color === 'success' ? 'bg-green-100' :
                  superavitStatus.color === 'warning' ? 'bg-yellow-100' :
                  'bg-red-100'
                }`}>
                  <StatusIcon className={`w-6 h-6 ${
                    superavitStatus.color === 'success' ? 'text-green-600' :
                    superavitStatus.color === 'warning' ? 'text-yellow-600' :
                    'text-red-600'
                  }`} />
                </div>
                <div>
                  <h3 className={`text-lg font-bold ${
                    superavitStatus.color === 'success' ? 'text-green-900' :
                    superavitStatus.color === 'warning' ? 'text-yellow-900' :
                    'text-red-900'
                  }`}>
                    Superávit: {formatPercentage(results.deficit_surplus_percentage)}
                  </h3>
                  <p className={`text-sm ${
                    superavitStatus.color === 'success' ? 'text-green-700' :
                    superavitStatus.color === 'warning' ? 'text-yellow-700' :
                    'text-red-700'
                  }`}>
                    Status: {superavitStatus.text}
                  </p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="text-right">
                <div className="text-3xl font-bold text-gray-800 mb-1">
                  {(results.deficit_surplus_percentage * 100).toFixed(0)}%
                </div>
                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-500 ${
                      superavitStatus.color === 'success' ? 'bg-green-500' :
                      superavitStatus.color === 'warning' ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${Math.min(100, results.deficit_surplus_percentage * 25)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Detailed breakdown */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Valor Total:</span>
                <div className="font-semibold text-gray-800">
                  {formatCurrency(results.rmba + results.rmbc)}
                </div>
              </div>
              <div>
                <span className="text-gray-600">Diferença:</span>
                <div className="font-semibold text-gray-800">
                  {formatCurrency(results.deficit_surplus)}
                </div>
              </div>
            </div>
          </div>

          {/* New sections for Replacement Ratios with clear labels */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Target Replacement Ratio */}
            <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-purple-700">Taxa de Reposição Alvo</span>
                <TrendingUp className="w-4 h-4 text-purple-600" />
              </div>
              <div className="text-2xl font-bold text-purple-900">
                {formatPercentage(results.target_replacement_ratio / 100)}
              </div>
              <p className="text-xs text-purple-600 mt-1">Benefício desejado / Salário Final</p>
            </div>

            {/* Sustainable Replacement Ratio */}
            <div className="bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg p-4 border border-orange-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-orange-700">Taxa de Reposição Sustentável</span>
                <TrendingUp className="w-4 h-4 text-orange-600" />
              </div>
              <div className="text-2xl font-bold text-orange-900">
                {formatPercentage(results.sustainable_replacement_ratio / 100)}
              </div>
              <p className="text-xs text-orange-600 mt-1">Quanto do benefício alvo pode ser pago</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ResultsCard;
