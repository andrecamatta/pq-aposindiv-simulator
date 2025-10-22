import React from 'react';
import { Line } from 'react-chartjs-2';
import { Card, Badge, Icon } from '../../design-system/components';
import { formatCurrencyBR } from '../../utils/formatBR';
import type { SimulatorResults, SimulatorState } from '../../types/simulator.types';

interface SurvivorIncomeChartProps {
  results: SimulatorResults;
  state: SimulatorState;
}

/**
 * Gráfico que mostra as rendas de sobrevivência (pensões) ao longo do tempo
 *
 * Mostra o benefício principal do titular e as pensões que cada
 * dependente receberia após o falecimento do titular.
 */
export function SurvivorIncomeChart({ results, state }: SurvivorIncomeChartProps) {
  const survivorAnalysis = results.survivor_analysis;

  if (!survivorAnalysis || !survivorAnalysis.survivor_details?.length) {
    return null;
  }

  const { survivor_details, vpa_survivor_benefits } = survivorAnalysis;
  const { projection_years, projected_benefits } = results;

  // Dataset do benefício principal
  const mainBenefitDataset = {
    label: 'Benefício Principal (Titular)',
    data: projected_benefits,
    borderColor: 'rgb(59, 130, 246)',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    borderWidth: 3,
    fill: true,
    tension: 0.4,
    pointRadius: 0,
    pointHoverRadius: 6
  };

  // Datasets de pensões para cada dependente
  const pensionDatasets = survivor_details.map((detail, index) => {
    const colors = [
      { border: 'rgb(16, 185, 129)', background: 'rgba(16, 185, 129, 0.1)' },   // Verde
      { border: 'rgb(245, 158, 11)', background: 'rgba(245, 158, 11, 0.1)' },   // Amarelo
      { border: 'rgb(239, 68, 68)', background: 'rgba(239, 68, 68, 0.1)' },     // Vermelho
      { border: 'rgb(139, 92, 246)', background: 'rgba(139, 92, 246, 0.1)' },   // Roxo
      { border: 'rgb(236, 72, 153)', background: 'rgba(236, 72, 153, 0.1)' }    // Rosa
    ];

    const color = colors[index % colors.length];

    return {
      label: `Pensão: ${detail.member_name} (${detail.survivor_percentage.toFixed(0)}%)`,
      data: detail.cash_flows,
      borderColor: color.border,
      backgroundColor: color.background,
      borderWidth: 2,
      borderDash: [5, 5],  // Linha tracejada para pensões
      fill: true,
      tension: 0.4,
      pointRadius: 0,
      pointHoverRadius: 6,
      pointHoverBackgroundColor: color.border,
      pointHoverBorderColor: '#fff',
      pointHoverBorderWidth: 2
    };
  });

  const chartData = {
    labels: projection_years,
    datasets: [mainBenefitDataset, ...pensionDatasets]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 15,
          font: {
            size: 12
          }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: {
          size: 14,
          weight: 'bold' as const
        },
        bodyFont: {
          size: 13
        },
        callbacks: {
          title: (context: any) => {
            return `Ano ${context[0].label}`;
          },
          label: (context: any) => {
            const value = context.parsed.y;
            return `${context.dataset.label}: ${formatCurrencyBR(value)}/ano`;
          },
          footer: (context: any) => {
            const total = context.reduce((sum: number, item: any) => sum + item.parsed.y, 0);
            return `\nTotal: ${formatCurrencyBR(total)}/ano`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Ano de Projeção',
          font: {
            size: 13,
            weight: 'bold' as const
          }
        },
        grid: {
          display: false
        }
      },
      y: {
        title: {
          display: true,
          text: 'Benefício Anual (R$)',
          font: {
            size: 13,
            weight: 'bold' as const
          }
        },
        beginAtZero: true,
        ticks: {
          callback: (value: any) => {
            if (value >= 1000000) {
              return `R$ ${(value / 1000000).toFixed(1)}M`;
            } else if (value >= 1000) {
              return `R$ ${(value / 1000).toFixed(0)}k`;
            }
            return `R$ ${value}`;
          }
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      }
    }
  };

  // Calcular total de rendas de sobrevivência (renda anual média)
  const totalSurvivorIncome = survivor_details.reduce(
    (sum, detail) => sum + (detail.cash_flows[0] || 0),
    0
  );

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <Icon name="heart" size={24} className="text-green-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Projeção de Rendas de Sobrevivência
            </h3>
            <p className="text-sm text-gray-600">
              Benefício do titular e pensões por morte para dependentes
            </p>
          </div>
        </div>

        <Badge variant="success">
          Proteção Familiar Ativa
        </Badge>
      </div>

      {/* Gráfico */}
      <div className="h-96 mb-6">
        <Line data={chartData} options={chartOptions} />
      </div>

      {/* Métricas de Proteção */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-6 border-t">
        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Icon name="shield" size={18} className="text-green-600" />
            <span className="text-sm font-medium text-green-900">
              VPA Pensões
            </span>
          </div>
          <div className="text-2xl font-bold text-green-900">
            {formatCurrencyBR(vpa_survivor_benefits)}
          </div>
          <p className="text-xs text-green-700 mt-1">
            Valor presente atuarial das pensões
          </p>
        </div>

        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Icon name="trending-up" size={18} className="text-blue-600" />
            <span className="text-sm font-medium text-blue-900">
              Renda Anual (1º ano)
            </span>
          </div>
          <div className="text-2xl font-bold text-blue-900">
            {formatCurrencyBR(totalSurvivorIncome)}
          </div>
          <p className="text-xs text-blue-700 mt-1">
            Total de pensões no primeiro ano
          </p>
        </div>

        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Icon name="percent" size={18} className="text-purple-600" />
            <span className="text-sm font-medium text-purple-900">
              Taxa de Reposição
            </span>
          </div>
          <div className="text-2xl font-bold text-purple-900">
            {((results.survivor_income_ratio || 0) * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-purple-700 mt-1">
            Renda sobrevivente / Benefício original
          </p>
        </div>

        <div className="bg-yellow-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Icon name="star" size={18} className="text-yellow-600" />
            <span className="text-sm font-medium text-yellow-900">
              Score de Proteção
            </span>
          </div>
          <div className="text-2xl font-bold text-yellow-900">
            {(results.family_protection_score || 0).toFixed(0)}
            <span className="text-sm font-normal">/100</span>
          </div>
          <p className="text-xs text-yellow-700 mt-1">
            Nível de proteção familiar
          </p>
        </div>
      </div>

      {/* Detalhamento por Pensão */}
      <div className="mt-6 pt-6 border-t">
        <h4 className="font-medium text-gray-900 mb-4">Pensões por Dependente</h4>
        <div className="space-y-3">
          {survivor_details.map((detail, index) => (
            <div
              key={detail.member_id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: pensionDatasets[index].borderColor }}
                />
                <div>
                  <span className="font-medium text-gray-900">{detail.member_name}</span>
                  {detail.eligible_until_age && !detail.is_disabled && (
                    <span className="ml-2 text-xs text-orange-600">
                      (Elegível até {detail.eligible_until_age} anos)
                    </span>
                  )}
                  {detail.is_disabled && (
                    <Badge variant="warning" size="sm" className="ml-2">
                      Vitalícia
                    </Badge>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-sm text-gray-600">% do Benefício</div>
                  <div className="font-semibold text-gray-900">
                    {detail.survivor_percentage.toFixed(1)}%
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-sm text-gray-600">VPA Pensão</div>
                  <div className="font-semibold text-gray-900">
                    {formatCurrencyBR(detail.vpa)}
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-sm text-gray-600">Renda Anual (1º ano)</div>
                  <div className="font-semibold text-gray-900">
                    {formatCurrencyBR(detail.cash_flows[0] || 0)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Explicação */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex gap-3">
          <Icon name="info" size={20} className="text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900">
            <p className="font-medium mb-1">Como interpretar este gráfico:</p>
            <ul className="list-disc list-inside space-y-1 text-blue-800">
              <li>
                <strong>Linha sólida azul:</strong> Benefício que o titular recebe enquanto vivo
              </li>
              <li>
                <strong>Linhas tracejadas:</strong> Pensões que cada dependente receberia após o falecimento do titular
              </li>
              <li>
                <strong>VPA (Valor Presente Atuarial):</strong> Valor atual de todos os pagamentos futuros, considerando mortalidade e desconto
              </li>
              <li>
                <strong>Score de Proteção:</strong> 0-100, baseado na cobertura das necessidades dos dependentes
              </li>
            </ul>
          </div>
        </div>
      </div>
    </Card>
  );
}
