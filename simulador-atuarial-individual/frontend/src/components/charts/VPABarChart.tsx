import React from 'react';
import { Icon } from '../../design-system/components/Icon';
import { Bar } from 'react-chartjs-2';
import type { SimulatorResults } from '../../types/simulator.types';
import { formatCurrencyBR } from '../../utils/formatBR';
import { getZeroLineGridConfig } from '../../utils/chartSetup';

interface VPABarChartProps {
  results: SimulatorResults;
}


const VPABarChart: React.FC<VPABarChartProps> = ({ results }) => {
  // Verificações de segurança
  if (!results) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="text-center">
          <Icon name="bar-chart" size="xl" className="text-gray-400 mb-4" />
          <p className="text-gray-500">Dados insuficientes para gerar o gráfico</p>
        </div>
      </div>
    );
  }

  // Dados recebidos validados

  // Decomposição da RMBA: VPA Benefícios - VPA Contribuições Futuras = RMBA
  // Validação robusta dos dados
  const rawVpaBenefits = results.actuarial_present_value_benefits;
  const rawVpaContributions = results.actuarial_present_value_salary;
  const rawRmba = results.rmba;

  // Se os valores específicos não estão disponíveis, mas temos RMBA, vamos calcular aproximações
  let vpaBenefits = 0;
  let vpaContributions = 0;

  if (rawVpaBenefits && !isNaN(rawVpaBenefits) && rawVpaBenefits > 0) {
    vpaBenefits = rawVpaBenefits;
  }

  if (rawVpaContributions && !isNaN(rawVpaContributions) && rawVpaContributions > 0) {
    vpaContributions = rawVpaContributions;
  }

  // Se não temos os dados diretos mas temos RMBA, mostrar explicação
  const hasValidVPAData = vpaBenefits > 0 || vpaContributions > 0;
  const rmba = rawRmba && !isNaN(rawRmba) ? rawRmba : 0;

  // Valores processados e validados

  // Se não temos dados VPA válidos, exibir uma mensagem mais informativa
  if (!hasValidVPAData && rmba !== 0) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="text-center">
          <Icon name="bar-chart" size="xl" className="text-gray-400 mb-4" />
          <div className="space-y-2">
            <p className="text-gray-700 font-medium">Decomposição da RMBA</p>
            <p className="text-sm text-gray-500">RMBA calculada: {formatCurrencyBR(rmba)}</p>
            <p className="text-xs text-gray-400">Aguardando cálculo dos componentes VPA</p>
          </div>
        </div>
      </div>
    );
  }
  
  const chartData = [vpaBenefits, -vpaContributions, rmba];

  const data = {
    labels: ['VPA Benefícios\na Conceder', '-VPA Contribuições\nFuturas', 'RMBA\n(VPA Benef - VPA Contrib)'],
    datasets: [
      {
        label: 'Valores Atuariais (R$)',
        data: chartData,
        backgroundColor: [
          'rgba(19, 164, 236, 0.6)',   // Primary blue softer
          'rgba(251, 146, 60, 0.6)',   // Softer orange-400
          'rgba(139, 92, 246, 0.6)',   // Softer violet-500
        ],
        borderColor: [
          'rgba(19, 164, 236, 0.8)',   // Primary blue
          'rgba(251, 146, 60, 0.8)',   // Orange-400
          'rgba(139, 92, 246, 0.8)',   // Violet-500
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
            return `${context.label}: ${formatCurrencyBR(value)}`;
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
        formatter: (value: number) => formatCurrencyBR(value),
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
            return formatCurrencyBR(value);
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
    <div className="h-[448px]"> {/* Aumentada de h-80 para h-[448px] (40% maior) para melhor visualização */}
      <Bar data={data} options={options} />
    </div>
  );
};

export default VPABarChart;