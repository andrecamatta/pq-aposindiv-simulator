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

  // Decomposição da RMBA: VPA Benefícios - VPA Contribuições Futuras = RMBA
  const vpaBenefits = isNaN(results.actuarial_present_value_benefits) ? 0 : results.actuarial_present_value_benefits;
  const vpaContributions = isNaN(results.actuarial_present_value_salary) ? 0 : results.actuarial_present_value_salary;
  const rmba = isNaN(results.rmba) ? 0 : results.rmba;
  
  const chartData = [vpaBenefits, -vpaContributions, rmba];

  const data = {
    labels: ['VPA Benefícios\na Conceder', '-VPA Contribuições\nFuturas', 'RMBA\n(VPA Benef - VPA Contrib)'],
    datasets: [
      {
        label: 'Valores Atuariais (R$)',
        data: chartData,
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',  // Azul para VPA Benefícios
          'rgba(245, 158, 11, 0.8)',  // Laranja para VPA Contribuições
          'rgba(99, 102, 241, 0.8)',  // Roxo para RMBA
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