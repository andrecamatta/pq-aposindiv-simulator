import React from 'react';
import { Line } from 'react-chartjs-2';
import type { SimulatorResults } from '../../types/simulator.types';
import { InfoTooltip } from '../../design-system/components';
import { getZeroLineGridConfig } from '../../utils/chartSetup';
import { formatCurrency } from '../../utils';

interface DeterministicChartProps {
  results: SimulatorResults;
  currentAge: number;
}


const DeterministicChart: React.FC<DeterministicChartProps> = ({ results, currentAge }) => {
  // Verificações de segurança
  if (!results || !results.projection_years || !Array.isArray(results.projection_years)) {
    return (
      <div className="h-[32rem] flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">📊</div>
          <p className="text-gray-500">Dados insuficientes para gerar o gráfico</p>
          <p className="text-sm text-gray-400">Configure os parâmetros e execute a simulação</p>
        </div>
      </div>
    );
  }

  // Calcular labels de idade baseadas na idade atual
  const ageLabels = results.projection_years.map(year => currentAge + year);
  
  // Simulação determinística - sem consideração de mortalidade
  
  const data = {
    labels: ageLabels,
    datasets: [
      {
        label: 'Salários Anuais (Valores Reais)',
        data: results.projected_salaries || [],
        borderColor: '#3B82F6',
        backgroundColor: '#3B82F6',
        tension: 0.4,
        fill: false,
        pointRadius: 2,
      },
      {
        label: 'Benefícios Anuais Projetados',
        data: results.projected_benefits || [],
        borderColor: '#10B981',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        tension: 0.4,
        fill: false,
        pointRadius: 2,
      },
      {
        label: 'Reservas Acumuladas (Determinística)',
        data: results.accumulated_reserves || [],
        borderColor: '#8B5CF6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const value = context.parsed.y;
            return `${context.dataset.label}: ${formatCurrency(value, 0)}`;
          },
        },
      },
      datalabels: {
        display: false,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Idade (anos)',
        },
        grid: {
          display: false,
        },
        ticks: {
          display: true,
          font: {
            size: 11,
          },
          color: '#6B7280',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Valores Anuais e Reservas (R$)',
        },
        grid: getZeroLineGridConfig(),
        ticks: {
          display: true,
          font: {
            size: 11,
          },
          color: '#6B7280',
          callback: function(value: any) {
            return formatCurrency(value, 0);
          },
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  };

  return (
    <div className="h-[32rem]">
      {/* Título com Tooltip Explicativo */}
      <div className="flex items-center gap-2 mb-4 px-1">
        <h3 className="text-lg font-semibold text-gray-900">
          Simulação Determinística - Evolução das Reservas
        </h3>
        <InfoTooltip 
          content="Simulação realística assumindo que você viverá durante todo período projetado. Mostra exatamente quanto dinheiro você terá em cada idade, considerando salários, contribuições e benefícios. Reservas negativas = dinheiro insuficiente. Esta é a realidade financeira da sua conta individual."
          iconSize={18}
        />
      </div>
      
      {/* Gráfico */}
      <div className="h-[26rem]">
        <Line data={data} options={options} />
      </div>
    </div>
  );
};

export default DeterministicChart;