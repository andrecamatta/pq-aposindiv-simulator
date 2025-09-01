import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import type { SimulatorResults } from '../../types/simulator.types';
import { formatCurrencyBR } from '../../utils/formatBR';

interface RMBACompositionChartProps {
  results: SimulatorResults;
}


const RMBACompositionChart: React.FC<RMBACompositionChartProps> = ({ results }) => {
  const data = {
    labels: ['VPA Benefícios Futuros', '-VPA Contribuições Futuras'],
    datasets: [
      {
        data: [
          results.actuarial_present_value_benefits,
          -results.actuarial_present_value_salary,
        ],
        backgroundColor: [
          '#EF4444',
          '#10B981',
        ],
        borderColor: [
          '#DC2626',
          '#059669',
        ],
        borderWidth: 2,
        hoverBackgroundColor: [
          '#F87171',
          '#34D399',
        ],
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          padding: 20,
          usePointStyle: true,
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
            const percentage = ((context.parsed / total) * 100).toFixed(1);
            return `${context.label}: ${formatCurrencyBR(context.parsed, 0)} (${percentage}%)`;
          },
        },
      },
    },
    cutout: '60%',
  };

  const centerValue = results.rmba;
  const centerText = formatCurrencyBR(centerValue, 0);

  return (
    <div className="relative h-80">
      <Doughnut data={data} options={options} />
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="text-xs text-gray-500 font-medium mb-1">RMBA</div>
        <div className="text-lg font-bold text-gray-900">{centerText}</div>
      </div>
    </div>
  );
};

export default RMBACompositionChart;