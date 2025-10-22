import React from 'react';
import { Line } from 'react-chartjs-2';
import { Card, Badge, Icon } from '../../design-system/components';
import { formatCurrencyBR } from '../../utils/formatBR';
import type { SimulatorResults, SimulatorState } from '../../types/simulator.types';

interface InheritanceValueChartProps {
  results: SimulatorResults;
  state: SimulatorState;
}

/**
 * Gráfico que mostra o valor da função de heritor por idade
 *
 * Para cada idade do titular, mostra quanto cada dependente herdaria
 * se o titular falecesse naquela idade específica.
 */
export function InheritanceValueChart({ results, state }: InheritanceValueChartProps) {
  const inheritanceAnalysis = results.survivor_analysis?.inheritance_analysis;

  if (!inheritanceAnalysis || !inheritanceAnalysis.inheritance_by_member?.length) {
    return null;
  }

  const { ages, inheritance_by_member, expected_inheritance_value } = inheritanceAnalysis;

  // Preparar dados para o gráfico
  const datasets = inheritance_by_member.map((member, index) => {
    const colors = [
      { border: 'rgb(59, 130, 246)', background: 'rgba(59, 130, 246, 0.1)' },   // Azul
      { border: 'rgb(16, 185, 129)', background: 'rgba(16, 185, 129, 0.1)' },   // Verde
      { border: 'rgb(245, 158, 11)', background: 'rgba(245, 158, 11, 0.1)' },   // Amarelo
      { border: 'rgb(239, 68, 68)', background: 'rgba(239, 68, 68, 0.1)' },     // Vermelho
      { border: 'rgb(139, 92, 246)', background: 'rgba(139, 92, 246, 0.1)' }    // Roxo
    ];

    const color = colors[index % colors.length];

    return {
      label: `${member.member_name} (${member.share_percentage.toFixed(0)}%)`,
      data: member.inheritance_value_by_age,
      borderColor: color.border,
      backgroundColor: color.background,
      borderWidth: 2,
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
    labels: ages,
    datasets
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
      title: {
        display: false
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
            return `Idade do Titular: ${context[0].label} anos`;
          },
          label: (context: any) => {
            const value = context.parsed.y;
            return `${context.dataset.label}: ${formatCurrencyBR(value)}`;
          },
          footer: (context: any) => {
            const total = context.reduce((sum: number, item: any) => sum + item.parsed.y, 0);
            return `\nTotal: ${formatCurrencyBR(total)}`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Idade do Titular (anos)',
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
          text: 'Valor da Herança (R$)',
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

  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Icon name="trending-up" size={24} className="text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Valor da Função de Heritor por Idade
            </h3>
            <p className="text-sm text-gray-600">
              Quanto cada dependente herdaria se o titular falecer em cada idade
            </p>
          </div>
        </div>

        <Badge variant="info">
          Plano CD
        </Badge>
      </div>

      {/* Gráfico */}
      <div className="h-96 mb-6">
        <Line data={chartData} options={chartOptions} />
      </div>

      {/* Resumo Estatístico */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t">
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Icon name="dollar-sign" size={18} className="text-purple-600" />
            <span className="text-sm font-medium text-purple-900">
              Valor Esperado de Herança
            </span>
          </div>
          <div className="text-2xl font-bold text-purple-900">
            {formatCurrencyBR(expected_inheritance_value)}
          </div>
          <p className="text-xs text-purple-700 mt-1">
            Valor médio ponderado por probabilidade de morte
          </p>
        </div>

        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Icon name="users" size={18} className="text-blue-600" />
            <span className="text-sm font-medium text-blue-900">
              Herdeiros
            </span>
          </div>
          <div className="text-2xl font-bold text-blue-900">
            {inheritance_by_member.length}
          </div>
          <p className="text-xs text-blue-700 mt-1">
            Dependentes com direito à herança
          </p>
        </div>

        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Icon name="calendar" size={18} className="text-green-600" />
            <span className="text-sm font-medium text-green-900">
              Horizonte de Projeção
            </span>
          </div>
          <div className="text-2xl font-bold text-green-900">
            {ages.length} anos
          </div>
          <p className="text-xs text-green-700 mt-1">
            De {ages[0]} a {ages[ages.length - 1]} anos
          </p>
        </div>
      </div>

      {/* Detalhamento por Herdeiro */}
      <div className="mt-6 pt-6 border-t">
        <h4 className="font-medium text-gray-900 mb-4">Detalhamento por Herdeiro</h4>
        <div className="space-y-3">
          {inheritance_by_member.map((member, index) => (
            <div
              key={member.member_id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: datasets[index].borderColor }}
                />
                <span className="font-medium text-gray-900">{member.member_name}</span>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <div className="text-sm text-gray-600">Participação</div>
                  <div className="font-semibold text-gray-900">
                    {member.share_percentage.toFixed(1)}%
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-sm text-gray-600">Valor Esperado</div>
                  <div className="font-semibold text-gray-900">
                    {formatCurrencyBR(member.expected_value)}
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
                <strong>Eixo X (horizontal):</strong> Idade do titular no momento do falecimento
              </li>
              <li>
                <strong>Eixo Y (vertical):</strong> Valor que cada herdeiro receberia
              </li>
              <li>
                <strong>Crescimento da curva:</strong> Representa o acúmulo de saldo ao longo do tempo
              </li>
              <li>
                <strong>Valor esperado:</strong> Média ponderada pela probabilidade de óbito em cada idade
              </li>
            </ul>
          </div>
        </div>
      </div>
    </Card>
  );
}
