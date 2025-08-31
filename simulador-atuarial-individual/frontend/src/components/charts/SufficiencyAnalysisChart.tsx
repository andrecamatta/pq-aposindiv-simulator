import React from 'react';
import { Bar } from 'react-chartjs-2';
import type { SimulatorResults, SimulatorState } from '../../types/simulator.types';
import { formatCurrency } from '../../utils';
import { getZeroLineGridConfig } from '../../utils/chartSetup';

interface SufficiencyAnalysisChartProps {
  results: SimulatorResults;
  state: SimulatorState;
}


const SufficiencyAnalysisChart: React.FC<SufficiencyAnalysisChartProps> = ({ results, state }) => {
  // Verificações de segurança
  if (!results || !state) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">⚖️</div>
          <p className="text-gray-500">Dados insuficientes para gerar o gráfico</p>
        </div>
      </div>
    );
  }

  // Análise de suficiência: Saldo Inicial + (-RMBA) = Déficit/Superávit
  const initialBalance = isNaN(state.initial_balance) ? 0 : state.initial_balance;
  const negativeRMBA = isNaN(results.rmba) ? 0 : -results.rmba;
  const deficitSurplus = isNaN(results.deficit_surplus) ? 0 : results.deficit_surplus;
  
  const chartData = [initialBalance, negativeRMBA, deficitSurplus];

  const data = {
    labels: ['Saldo\nInicial', '-RMBA\n(Passivo Reduzido)', 'Déficit/Superávit\n(Resultado)'],
    datasets: [
      {
        label: 'Análise de Suficiência (R$)',
        data: chartData,
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',  // Azul para Saldo Inicial
          'rgba(245, 158, 11, 0.8)',  // Laranja para -RMBA
          'rgba(99, 102, 241, 0.8)',  // Roxo para resultado final
        ],
        borderColor: [
          'rgb(59, 130, 246)',        // Azul
          'rgb(245, 158, 11)',        // Laranja
          'rgb(99, 102, 241)',        // Roxo
        ],
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    layout: {
      padding: {
        top: 40, // Espaço para rótulos superiores
        bottom: 10,
        left: 10,
        right: 10,
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const value = context.parsed.y;
            return `${context.label}: ${formatCurrency(value)}`;
          },
        },
      },
      datalabels: {
        display: true,
        anchor: 'end' as const,
        align: (context: any) => {
          // Para valores negativos, posiciona abaixo da barra
          const value = context.parsed?.y ?? context.raw;
          return value < 0 ? 'bottom' : 'top';
        },
        formatter: (value: number) => formatCurrency(value),
        font: {
          size: 11,
          weight: 'bold' as const,
        },
        color: '#374151',
        clamp: true, // Garante que os rótulos ficam dentro da área visível
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 11,
            weight: 'bold' as const,
          },
          color: '#6B7280',
        },
      },
      y: {
        beginAtZero: false,
        grid: getZeroLineGridConfig(),
        ticks: {
          font: {
            size: 11,
          },
          color: '#6B7280',
          callback: function(value: any) {
            return formatCurrency(value);
          },
        },
        title: {
          display: true,
          text: 'Valores (R$)',
          font: {
            size: 12,
            weight: 'bold' as const,
          },
          color: '#374151',
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  };

  return (
    <div className="space-y-3">      
      {/* Gráfico */}
      <div className="h-[448px]"> {/* Aumentada de h-80 para h-[448px] (40% maior) para melhor visualização */}
        <Bar data={data} options={options} />
      </div>
      
      {/* Explicação da Fórmula */}
      <div className="bg-gray-50 rounded-lg p-3">
        <div className="text-center text-sm text-gray-600">
          <div className="font-medium mb-1">Equação de Suficiência Financeira:</div>
          <div className="font-mono text-xs">
            <span className="text-blue-600">Saldo Inicial</span>
            {" + "}
            <span className="text-orange-600">(-RMBA)</span>
            {" = "}
            <span className="text-indigo-600">
              {deficitSurplus >= 0 ? 'Superávit' : 'Déficit'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SufficiencyAnalysisChart;