import React from 'react';
import { BarChart3, TrendingUp, TrendingDown, CheckCircle, AlertTriangle, Target, DollarSign, PieChart, Clock } from 'lucide-react';
import type { SimulatorResults } from '../types';
import { formatCurrency, formatPercentage } from '../utils/formatting';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent, 
  Badge,
  Table,
  TableBody,
  TableRow,
  TableCell,
  SkeletonCard
} from '../design-system/components';

interface ResultsDashboardProps {
  results: SimulatorResults | null;
  loading: boolean;
}

const ResultsDashboard: React.FC<ResultsDashboardProps> = ({ results, loading }) => {
  if (loading) {
    return (
      <div className="space-y-6">
        {/* Loading Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        
        <SkeletonCard />
        <SkeletonCard />
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
          <p className="text-sm">Configure os parâmetros à esquerda para visualizar os resultados</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* KPI Cards - S-Tier Design */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* RMBA Card */}
        <Card variant="default" padding="md" className="hover:shadow-card-hover transition-all duration-200">
          <div className="flex items-center justify-between mb-4">
            <Badge variant="primary" size="sm" className="uppercase font-semibold">
              RMBA
            </Badge>
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-primary-600" />
            </div>
          </div>
          <div className="text-2xl font-bold text-gray-900 mb-1">
            {formatCurrency(results.rmba)}
          </div>
          <div className="text-sm text-gray-500">
            Reserva Benefícios a Conceder
          </div>
        </Card>

        {/* RMBC Card */}
        <Card variant="default" padding="md" className="hover:shadow-card-hover transition-all duration-200">
          <div className="flex items-center justify-between mb-4">
            <Badge variant="success" size="sm" className="uppercase font-semibold">
              RMBC
            </Badge>
            <div className="w-10 h-10 bg-success-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-success-600" />
            </div>
          </div>
          <div className="text-2xl font-bold text-gray-900 mb-1">
            {formatCurrency(results.rmbc)}
          </div>
          <div className="text-sm text-gray-500">
            Reserva Benefícios Concedidos
          </div>
        </Card>

        {/* Déficit/Superávit Card */}
        <Card 
          variant="default" 
          padding="md" 
          className={`hover:shadow-card-hover transition-all duration-200 ${
            (results.deficit_surplus || 0) >= 0 
              ? 'bg-gradient-to-br from-success-50 to-success-100 border-success-200' 
              : 'bg-gradient-to-br from-error-50 to-error-100 border-error-200'
          }`}
        >
          <div className="flex items-center justify-between mb-4">
            <Badge 
              variant={(results.deficit_surplus || 0) >= 0 ? 'success-solid' : 'error-solid'} 
              size="sm" 
              className="uppercase font-semibold"
            >
              {(results.deficit_surplus || 0) >= 0 ? 'Superávit' : 'Déficit'}
            </Badge>
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              (results.deficit_surplus || 0) >= 0 ? 'bg-success-100' : 'bg-error-100'
            }`}>
              {(results.deficit_surplus || 0) >= 0 ? (
                <TrendingUp className="w-5 h-5 text-success-600" />
              ) : (
                <TrendingDown className="w-5 h-5 text-error-600" />
              )}
            </div>
          </div>
          <div className={`text-2xl font-bold mb-1 ${
            (results.deficit_surplus || 0) >= 0 ? 'text-success-700' : 'text-error-700'
          }`}>
            {formatCurrency(Math.abs(results.deficit_surplus || 0))}
          </div>
          <div className="text-sm text-gray-500">
            {formatPercentage(Math.abs(results.deficit_surplus_percentage || 0))}
          </div>
        </Card>
      </div>

      {/* Métricas Secundárias - S-Tier Design */}
      <Card variant="default" padding="md">
        <CardHeader withBorder>
          <CardTitle className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
              <Target className="w-5 h-5 text-primary-600" />
            </div>
            Métricas-Chave
          </CardTitle>
        </CardHeader>
        
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Taxa Necessária */}
            <div className="text-center group">
              <div className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center mb-3 transition-all duration-200 group-hover:scale-105 ${
                (results.required_contribution_rate || 0) <= 8
                  ? 'bg-success-100 text-success-600 group-hover:bg-success-200' 
                  : 'bg-error-100 text-error-600 group-hover:bg-error-200'
              }`}>
                <span className="text-lg font-bold">
                  {(results.required_contribution_rate || 0).toFixed(1)}%
                </span>
              </div>
              <div className="text-sm font-medium text-gray-600">Taxa Necessária</div>
            </div>

            {/* Total Contribuições */}
            <div className="text-center group">
              <div className="w-16 h-16 mx-auto bg-primary-100 text-primary-600 rounded-full flex items-center justify-center mb-3 transition-all duration-200 group-hover:scale-105 group-hover:bg-primary-200">
                <DollarSign className="w-6 h-6" />
              </div>
              <div className="text-lg font-bold text-gray-900 mb-1">
                {(results.total_contributions / 1000000).toFixed(1)}M
              </div>
              <div className="text-sm font-medium text-gray-600">Total Contribuições</div>
            </div>

            {/* Total Benefícios */}
            <div className="text-center group">
              <div className="w-16 h-16 mx-auto bg-info-100 text-info-600 rounded-full flex items-center justify-center mb-3 transition-all duration-200 group-hover:scale-105 group-hover:bg-info-200">
                <PieChart className="w-6 h-6" />
              </div>
              <div className="text-lg font-bold text-gray-900 mb-1">
                {(results.total_benefits / 1000000).toFixed(1)}M
              </div>
              <div className="text-sm font-medium text-gray-600">Total Benefícios</div>
            </div>

            {/* Duration */}
            <div className="text-center group">
              <div className="w-16 h-16 mx-auto bg-warning-100 text-warning-600 rounded-full flex items-center justify-center mb-3 transition-all duration-200 group-hover:scale-105 group-hover:bg-warning-200">
                <Clock className="w-6 h-6" />
              </div>
              <div className="text-lg font-bold text-gray-900 mb-1">
                {results.liability_duration.toFixed(1)}
              </div>
              <div className="text-sm font-medium text-gray-600">Duration (anos)</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Decomposição Atuarial - Professional Table */}
      <Card variant="default" padding="lg">
        <CardHeader withBorder>
          <CardTitle className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <span className="text-purple-600 text-lg">⚖️</span>
            </div>
            Decomposição Atuarial
          </CardTitle>
        </CardHeader>
        
        <CardContent className="pt-6">
          <Table>
            <TableBody>
              <TableRow>
                <TableCell className="font-medium text-gray-600">VPA Benefícios Futuros</TableCell>
                <TableCell numeric className="font-bold text-gray-900">
                  {formatCurrency(results.actuarial_present_value_benefits)}
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium text-gray-600">VPA Salários Futuros</TableCell>
                <TableCell numeric className="font-bold text-gray-900">
                  {formatCurrency(results.actuarial_present_value_salary)}
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium text-gray-600">Convexidade</TableCell>
                <TableCell numeric className="font-bold text-gray-900">
                  {results.convexity.toFixed(2)}
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium text-gray-600">Método Atuarial</TableCell>
                <TableCell numeric className="font-bold text-gray-900">
                  {results.actuarial_method_details.method || 'N/A'}
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium text-gray-600">Tempo de Cálculo</TableCell>
                <TableCell numeric className="font-bold text-gray-900">
                  {results.computation_time_ms.toFixed(1)}ms
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="font-medium text-gray-600">Calculado em</TableCell>
                <TableCell numeric className="font-medium text-gray-600">
                  {new Date(results.calculation_timestamp).toLocaleString('pt-BR')}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Status de Validação */}
      <Card variant="default" padding="lg">
        <CardHeader withBorder>
          <CardTitle className="flex items-center gap-3">
            <div className="w-10 h-10 bg-success-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-success-600" />
            </div>
            Status de Validação
          </CardTitle>
        </CardHeader>
        
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-3">
            {Object.entries(results.assumptions_validation).map(([key, isValid]) => (
              <Badge
                key={key}
                variant={isValid ? 'success' : 'error'}
                size="md"
                className="font-medium"
                leftIcon={
                  <span className="text-xs">
                    {isValid ? '✓' : '✗'}
                  </span>
                }
              >
                {key}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResultsDashboard;