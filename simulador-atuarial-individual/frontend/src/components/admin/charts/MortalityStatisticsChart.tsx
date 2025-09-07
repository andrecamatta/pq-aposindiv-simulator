import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import type { TableStatistics } from '../hooks/useMortalityTables';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface MortalityStatisticsChartProps {
  statistics: TableStatistics;
}

const MortalityStatisticsChart: React.FC<MortalityStatisticsChartProps> = ({
  statistics
}) => {
  const { age_groups } = statistics.statistics;

  const chartData = {
    labels: [
      `Jovens (${age_groups.young.ages})`,
      `Adultos (${age_groups.adult.ages})`,
      `Idosos (${age_groups.elderly.ages})`
    ],
    datasets: [
      {
        label: 'Taxa Média de Mortalidade por Faixa Etária',
        data: [
          age_groups.young.avg_qx,
          age_groups.adult.avg_qx,
          age_groups.elderly.avg_qx
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.6)',   // green for young
          'rgba(251, 191, 36, 0.6)',  // yellow for adult
          'rgba(239, 68, 68, 0.6)',   // red for elderly
        ],
        borderColor: [
          'rgb(34, 197, 94)',
          'rgb(251, 191, 36)',
          'rgb(239, 68, 68)',
        ],
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: `Análise por Faixa Etária - ${statistics.table_info.name}`,
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const value = context.parsed.y;
            return `Taxa média: ${(value * 1000).toFixed(3)}‰`;
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Faixa Etária',
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Taxa Média de Mortalidade',
        },
        ticks: {
          callback: function(value: any) {
            return (value * 1000).toFixed(1) + '‰';
          },
        },
      },
    },
  };

  return (
    <div className="w-full h-96 p-4 bg-white">
      <Bar data={chartData} options={options} />
    </div>
  );
};

export default MortalityStatisticsChart;