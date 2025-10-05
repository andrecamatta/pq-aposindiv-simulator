import React from 'react';
import { Line } from 'react-chartjs-2';
import { Icon } from '../../design-system/components/Icon';
import { InfoTooltip } from '../../design-system/components';
import { getZeroLineGridConfig } from '../../utils/chartSetup';
import { formatCurrencyBR } from '../../utils/formatBR';
import type { SimulatorResults } from '../../types/simulator.types';

interface ChartDataset {
  label: string;
  data: number[];
  borderColor: string;
  backgroundColor: string;
  tension?: number;
  fill?: boolean;
  pointRadius?: number;
  borderDash?: number[];
  borderWidth?: number;
}

interface BaseProjectionChartProps {
  results: SimulatorResults;
  currentAge: number;
  title: string;
  tooltipContent: string;
  datasets: ChartDataset[];
  yAxisLabel?: string;
  height?: string;
  showCurrencyTooltip?: boolean;
}

export const BaseProjectionChart: React.FC<BaseProjectionChartProps> = ({
  results,
  currentAge,
  title,
  tooltipContent,
  datasets,
  yAxisLabel = 'Valores (R$)',
  height = 'h-[26rem]',
  showCurrencyTooltip = true
}) => {
  // Validação unificada
  if (!results || !results.projection_years || !Array.isArray(results.projection_years)) {
    return (
      <div className={`${height} flex items-center justify-center`}>
        <div className="text-center">
          <Icon name="bar-chart" size="xl" className="text-gray-400 mb-4" />
          <p className="text-gray-500">Dados insuficientes para gerar o gráfico</p>
          <p className="text-sm text-gray-400">Configure os parâmetros e execute a simulação</p>
        </div>
      </div>
    );
  }

  // Calcular labels de idade
  const ageLabels = results.projection_years.map(year => currentAge + year);

  // Configuração unificada de options
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: { size: 12 }
        }
      },
      tooltip: {
        callbacks: showCurrencyTooltip ? {
          label: function(context: any) {
            const value = context.parsed.y;
            return `${context.dataset.label}: ${formatCurrencyBR(value)}`;
          }
        } : undefined
      },
      datalabels: { display: false }
    },
    scales: {
      x: {
        title: { display: true, text: 'Idade (anos)' },
        grid: { display: false },
        ticks: {
          display: true,
          font: { size: 11 },
          color: '#6B7280'
        }
      },
      y: {
        title: { display: true, text: yAxisLabel },
        grid: getZeroLineGridConfig(),
        ticks: {
          display: true,
          font: { size: 11 },
          color: '#6B7280',
          callback: function(value: any) {
            return formatCurrencyBR(value);
          }
        }
      }
    },
    interaction: {
      intersect: false,
      mode: 'index' as const
    }
  };

  const data = {
    labels: ageLabels,
    datasets
  };

  return (
    <div className={height}>
      <div className="flex items-center gap-2 mb-4 px-1">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <InfoTooltip content={tooltipContent} iconSize={18} />
      </div>
      <div className="h-[21rem]">
        <Line data={data} options={options} />
      </div>
    </div>
  );
};
