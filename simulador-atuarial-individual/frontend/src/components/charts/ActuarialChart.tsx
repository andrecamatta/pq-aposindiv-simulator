import React from 'react';
import { Icon } from '../../design-system/components/Icon';
import { Line } from 'react-chartjs-2';
import type { SimulatorResults } from '../../types/simulator.types';
import { formatCurrencyBR } from '../../utils/formatBR';
import { InfoTooltip } from '../../design-system/components';
import { getZeroLineGridConfig } from '../../utils/chartSetup';

interface ActuarialChartProps {
  results: SimulatorResults;
  currentAge: number;
}


const ActuarialChart: React.FC<ActuarialChartProps> = ({ results, currentAge }) => {
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
  
  // Usar dados reais do backend para projeções atuariais
  const vpaBenefits = results.projected_vpa_benefits || [];
  const vpaContributions = results.projected_vpa_contributions || [];
  const rmbaEvolution = results.projected_rmba_evolution || [];

  const data = {
    labels: ageLabels,
    datasets: [
      {
        label: 'VPA Benefícios Futuros',
        data: vpaBenefits,
        borderColor: '#DC2626',
        backgroundColor: 'transparent',
        tension: 0.4,
        fill: false,
        pointRadius: 2,
        borderDash: [5, 5],
      },
      {
        label: 'VPA Contribuições Futuras',
        data: vpaContributions,
        borderColor: '#059669',
        backgroundColor: 'transparent',
        tension: 0.4,
        fill: false,
        pointRadius: 2,
        borderDash: [3, 3],
      },
      {
        label: 'RMBA (Reserva Matemática)',
        data: rmbaEvolution,
        borderColor: '#7C3AED',
        backgroundColor: 'rgba(124, 58, 237, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 3,
        borderWidth: 2,
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
            return `${context.dataset.label}: ${formatCurrencyBR(value)}`;
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
          text: 'Valores Presentes Atuariais (R$)',
        },
        grid: getZeroLineGridConfig(),
        ticks: {
          display: true,
          font: {
            size: 11,
          },
          color: '#6B7280',
          callback: function(value: any) {
            return formatCurrencyBR(value);
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
          Análise Atuarial - Considerando Mortalidade
        </h3>
        <InfoTooltip 
          content="Valores Presentes Atuariais (VPA) que consideram probabilidades de sobrevivência da tábua de mortalidade. VPA dos Benefícios = valor presente dos benefícios futuros ponderados pela probabilidade de estar vivo para recebê-los. RMBA = diferença entre VPA benefícios e VPA contribuições. Usado para cálculos regulatórios e análise de suficiência."
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

export default ActuarialChart;