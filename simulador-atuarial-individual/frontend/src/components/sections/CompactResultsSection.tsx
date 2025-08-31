import React, { useState } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Eye, CheckCircle, AlertTriangle, Target, DollarSign, PieChart, Clock, Info } from 'lucide-react';
import type { SimulatorResults } from '../../types';
import { formatCurrency, formatPercentage } from '../../utils/formatting';
import { Card, CardHeader, CardTitle, CardContent, Badge, Modal, ModalFooter, Button } from '../../design-system/components';

interface CompactResultsSectionProps {
  results: SimulatorResults | null;
  loading: boolean;
}

const CompactResultsSection: React.FC<CompactResultsSectionProps> = ({ results, loading }) => {
  const [showDetailModal, setShowDetailModal] = useState(false);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="text-center pb-2">
          <h2 className="text-lg font-bold text-slate-800 mb-1">Resultados</h2>
          <p className="text-sm text-slate-500">Calculando simulação...</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} padding="md">
              <div className="animate-pulse">
                <div className="flex items-center justify-between mb-3">
                  <div className="h-4 bg-gray-200 rounded w-16"></div>
                  <div className="w-8 h-8 bg-gray-200 rounded-lg"></div>
                </div>
                <div className="h-8 bg-gray-200 rounded w-24 mb-1"></div>
                <div className="h-3 bg-gray-200 rounded w-20"></div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <Card padding="lg">
        <div className="text-center text-gray-500">
          <div className="w-16 h-16 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
            <BarChart3 className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Resultados da Simulação</h3>
          <p className="text-sm">Configure os parâmetros para visualizar os resultados</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-2">
        <div className="text-center flex-1">
          <h2 className="text-lg font-bold text-slate-800 mb-1">Resultados</h2>
          <p className="text-sm text-slate-500">Principais indicadores</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowDetailModal(true)}
          className="flex items-center gap-2"
        >
          <Eye className="w-4 h-4" />
          Detalhes
        </Button>
      </div>

      {/* KPI Cards Principais */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* RMBA Card */}
        <Card variant="default" padding="sm" className="hover:shadow-card-hover transition-all duration-200">
          <div className="flex items-center justify-between mb-2">
            <Badge variant="primary" size="sm" className="uppercase font-semibold text-xs">
              RMBA
            </Badge>
            <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-primary-600" />
            </div>
          </div>
          <div className="text-lg font-bold text-gray-900 mb-1">
            {formatCurrency(results.rmba)}
          </div>
          <div className="text-xs text-gray-500">
            Reserva Benefícios a Conceder
          </div>
        </Card>

        {/* RMBC Card */}
        <Card variant="default" padding="sm" className="hover:shadow-card-hover transition-all duration-200">
          <div className="flex items-center justify-between mb-2">
            <Badge variant="success" size="sm" className="uppercase font-semibold text-xs">
              RMBC
            </Badge>
            <div className="w-8 h-8 bg-success-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-4 h-4 text-success-600" />
            </div>
          </div>
          <div className="text-lg font-bold text-gray-900 mb-1">
            {formatCurrency(results.rmbc)}
          </div>
          <div className="text-xs text-gray-500">
            Reserva Benefícios Concedidos
          </div>
        </Card>

        {/* Déficit/Superávit Card */}
        <Card 
          variant="default" 
          padding="sm" 
          className={`hover:shadow-card-hover transition-all duration-200 ${
            (results.deficit_surplus || 0) >= 0 
              ? 'bg-gradient-to-br from-success-50 to-success-100 border-success-200' 
              : 'bg-gradient-to-br from-error-50 to-error-100 border-error-200'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <Badge 
              variant={(results.deficit_surplus || 0) >= 0 ? 'success-solid' : 'error-solid'} 
              size="sm" 
              className="uppercase font-semibold text-xs"
            >
              {(results.deficit_surplus || 0) >= 0 ? 'Superávit' : 'Déficit'}
            </Badge>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              (results.deficit_surplus || 0) >= 0 ? 'bg-success-100' : 'bg-error-100'
            }`}>
              {(results.deficit_surplus || 0) >= 0 ? (
                <TrendingUp className="w-4 h-4 text-success-600" />
              ) : (
                <TrendingDown className="w-4 h-4 text-error-600" />
              )}
            </div>
          </div>
          <div className={`text-lg font-bold mb-1 ${
            (results.deficit_surplus || 0) >= 0 ? 'text-success-700' : 'text-error-700'
          }`}>
            {formatCurrency(Math.abs(results.deficit_surplus || 0))}
          </div>
          <div className="text-xs text-gray-500">
            {formatPercentage(Math.abs(results.deficit_surplus_percentage || 0))}
          </div>
        </Card>
      </div>

      {/* Métricas Compactas */}
      <Card variant="default" padding="sm">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center">
            <div className={`text-sm font-bold mb-1 ${
              (results.required_contribution_rate || 0) <= 8
                ? 'text-success-600' 
                : 'text-error-600'
            }`}>
              {(results.required_contribution_rate || 0).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600">Taxa Necessária</div>
          </div>
          <div className="text-center">
            <div className="text-sm font-bold text-gray-900 mb-1">
              {(results.total_contributions / 1000000).toFixed(1)}M
            </div>
            <div className="text-xs text-gray-600">Total Contribuições</div>
          </div>
          <div className="text-center">
            <div className="text-sm font-bold text-gray-900 mb-1">
              {(results.total_benefits / 1000000).toFixed(1)}M
            </div>
            <div className="text-xs text-gray-600">Total Benefícios</div>
          </div>
          <div className="text-center">
            <div className="text-sm font-bold text-gray-900 mb-1">
              {results.liability_duration.toFixed(1)}
            </div>
            <div className="text-xs text-gray-600">Duration (anos)</div>
          </div>
        </div>
      </Card>

      {/* Modal de Detalhes */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        title="Decomposição Atuarial Detalhada"
        subtitle="Informações técnicas e validação"
        size="lg"
      >
        <div className="space-y-6">
          {/* Decomposição Atuarial */}
          <div>
            <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
                <span className="text-purple-600 text-sm">⚖️</span>
              </div>
              Decomposição Atuarial
            </h3>
            
            <div className="overflow-hidden border border-slate-200 rounded-lg">
              <table className="w-full">
                <tbody className="divide-y divide-gray-100">
                  <tr className="hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm font-medium text-gray-600">VPA Benefícios Futuros</td>
                    <td className="py-3 px-4 text-sm font-bold text-gray-900 text-right">
                      {formatCurrency(results.actuarial_present_value_benefits)}
                    </td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm font-medium text-gray-600">VPA Salários Futuros</td>
                    <td className="py-3 px-4 text-sm font-bold text-gray-900 text-right">
                      {formatCurrency(results.actuarial_present_value_salary)}
                    </td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm font-medium text-gray-600">Convexidade</td>
                    <td className="py-3 px-4 text-sm font-bold text-gray-900 text-right">
                      {results.convexity.toFixed(2)}
                    </td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm font-medium text-gray-600">Método Atuarial</td>
                    <td className="py-3 px-4 text-sm font-bold text-gray-900 text-right">
                      {results.actuarial_method_details.method || 'N/A'}
                    </td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm font-medium text-gray-600">Tempo de Cálculo</td>
                    <td className="py-3 px-4 text-sm font-bold text-gray-900 text-right">
                      {results.computation_time_ms.toFixed(1)}ms
                    </td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm font-medium text-gray-600">Calculado em</td>
                    <td className="py-3 px-4 text-xs font-medium text-gray-600 text-right">
                      {new Date(results.calculation_timestamp).toLocaleString('pt-BR')}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Status de Validação */}
          <div>
            <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                <span className="text-green-600 text-sm">✅</span>
              </div>
              Status de Validação
            </h3>
            
            <div className="flex flex-wrap gap-2">
              {Object.entries(results.assumptions_validation).map(([key, isValid]) => (
                <span
                  key={key}
                  className={`inline-flex items-center px-3 py-2 rounded-full text-sm font-medium ${
                    isValid 
                      ? 'bg-green-100 text-green-800 border border-green-200' 
                      : 'bg-red-100 text-red-800 border border-red-200'
                  }`}
                >
                  <span className="mr-2">{isValid ? '✓' : '✗'}</span>
                  {key}
                </span>
              ))}
            </div>
          </div>
        </div>

        <ModalFooter>
          <Button variant="outline" onClick={() => setShowDetailModal(false)}>
            Fechar
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default CompactResultsSection;