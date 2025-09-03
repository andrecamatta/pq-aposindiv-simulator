import React from 'react';
import { Icon } from '../../design-system/components/Icon';
import { Line } from 'react-chartjs-2';
import type { SimulatorResults } from '../../types/simulator.types';
import { InfoTooltip } from '../../design-system/components';
import { getZeroLineGridConfig } from '../../utils/chartSetup';
import { formatCurrencyBR } from '../../utils/formatBR';

interface DeterministicChartProps {
  results: SimulatorResults;
  currentAge: number;
  planType?: string;
}


const DeterministicChart: React.FC<DeterministicChartProps> = ({ results, currentAge, planType }) => {
  // Verificações de segurança
  if (!results || !results.projection_years || !Array.isArray(results.projection_years)) {
    return (
      <div className="h-[32rem] flex items-center justify-center">
        <div className="text-center">
          <Icon name="bar-chart" size="xl" className="text-gray-400 mb-4" />
          <p className="text-gray-500">Dados insuficientes para gerar o gráfico</p>
          <p className="text-sm text-gray-400">Configure os parâmetros e execute a simulação</p>
        </div>
      </div>
    );
  }

  // Calcular labels de idade baseadas na idade atual
  const ageLabels = results.projection_years.map(year => currentAge + year);
  
  // Determinar labels conforme o tipo de plano
  const isCDPlan = planType === 'CD';
  const reserveLabel = isCDPlan ? 'Saldo Individual CD' : 'Reservas Acumuladas (Determinística)';
  const benefitLabel = isCDPlan ? 'Renda CD Anual' : 'Benefícios Anuais Projetados';
  
  const data = {
    labels: ageLabels,
    datasets: [
      {
        label: 'Salários Anuais (Valores Reais)',
        data: results.projected_salaries || [],
        borderColor: '#13a4ec', // primary color
        backgroundColor: '#13a4ec',
        tension: 0.4,
        fill: false,
        pointRadius: 2,
      },
      {
        label: benefitLabel,
        data: results.projected_benefits || [],
        borderColor: '#34D399', // softer emerald-400
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        tension: 0.4,
        fill: false,
        pointRadius: 2,
      },
      {
        label: reserveLabel,
        data: results.accumulated_reserves || [],
        borderColor: '#A78BFA', // softer violet-400
        backgroundColor: 'rgba(167, 139, 250, 0.1)',
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
            return `${context.dataset.label}: ${formatCurrencyBR(value, 0)}`;
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
            return formatCurrencyBR(value, 0);
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