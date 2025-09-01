import React from 'react';
import { Icon } from '../../design-system/components/Icon';
import { Bar } from 'react-chartjs-2';
import type { SimulatorResults, SimulatorState } from '../../types/simulator.types';
import { getZeroLineGridConfig } from '../../utils/chartSetup';
import { formatPercentageBR } from '../../utils/formatBR';

interface SufficiencyBarChartProps {
  results: SimulatorResults;
  state: SimulatorState;
}

const SufficiencyBarChart: React.FC<SufficiencyBarChartProps> = ({ results, state }) => {
  // Verificações de segurança
  if (!results || !state) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="text-center">
          <Icon name="trending-up" size="xl" className="text-gray-400 mb-4" />
          <p className="text-gray-500">Dados insuficientes para gerar o gráfico</p>
        </div>
      </div>
    );
  }

  // Calcular taxa de reposição alvo e sustentável com fallbacks
  const targetRate = isNaN(state.target_replacement_rate) ? 0 : (state.target_replacement_rate || 0);
  const sustainableRate = isNaN(results.replacement_ratio) ? 0 : results.replacement_ratio;
  
  // Determinar cores baseadas na comparação
  const getBarColor = (index: number) => {
    if (index === 0) return 'rgba(59, 130, 246, 0.8)'; // Azul para meta
    
    // Verde se sustentável >= meta, vermelho caso contrário
    if (sustainableRate >= targetRate) {
      return 'rgba(16, 185, 129, 0.8)'; // Verde
    } else {
      return 'rgba(239, 68, 68, 0.8)'; // Vermelho
    }
  };

  const getBorderColor = (index: number) => {
    if (index === 0) return 'rgb(59, 130, 246)';
    return sustainableRate >= targetRate ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)';
  };
  
  const data = {
    labels: ['Taxa Alvo', 'Taxa Sustentável'],
    datasets: [
      {
        label: 'Taxa de Reposição (%)',
        data: [targetRate, sustainableRate],
        backgroundColor: [
          getBarColor(0),
          getBarColor(1),
        ],
        borderColor: [
          getBorderColor(0),
          getBorderColor(1),
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
            return `${context.label}: ${formatPercentageBR(value)}`;
          },
        },
      },
      datalabels: {
        display: true,
        anchor: 'end' as const,
        align: 'top' as const,
        formatter: (value: number) => formatPercentageBR(value),
        font: {
          size: 12,
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
        beginAtZero: true,
        grid: getZeroLineGridConfig(),
        ticks: {
          font: {
            size: 11,
          },
          color: '#6B7280',
          callback: function(value: any) {
            return formatPercentageBR(value);
          },
        },
        title: {
          display: true,
          text: 'Taxa de Reposição (%)',
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
      {/* Indicadores de Status */}
      <div className="flex justify-center">
        <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
          sustainableRate >= targetRate 
            ? 'bg-green-100 text-green-800'
            : 'bg-red-100 text-red-800'
        }`}>
          <div className="flex items-center gap-2">
            {sustainableRate >= targetRate ? (
              <>
                <Icon name="check-circle" size="sm" className="text-green-600" />
                <span>Meta Alcançada</span>
              </>
            ) : (
              <>
                <Icon name="alert-triangle" size="sm" className="text-yellow-600" />
                <span>Meta Não Alcançada</span>
              </>
            )}
          </div>
        </div>
      </div>
      
      {/* Gráfico */}
      <div className="h-72"> {/* Aumentada de h-56 para h-72 para acomodar rótulos */}
        <Bar data={data} options={options} />
      </div>
      
      {/* Análise de Gap */}
      <div className="text-center text-sm text-gray-600">
        <span className="font-medium">
          Gap: {formatPercentageBR(Math.abs(sustainableRate - targetRate))}
        </span>
        {sustainableRate < targetRate && (
          <span className="text-red-600 ml-1">(Déficit)</span>
        )}
        {sustainableRate > targetRate && (
          <span className="text-green-600 ml-1">(Excedente)</span>
        )}
      </div>
    </div>
  );
};

export default SufficiencyBarChart;