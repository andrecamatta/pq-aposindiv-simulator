import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface MortalityRateData {
  age: number;
  qx: number;
}

interface MortalityRateChartProps {
  data: MortalityRateData[];
  tableName: string;
  color?: string;
}

const MortalityRateChart: React.FC<MortalityRateChartProps> = ({
  data,
  tableName,
  color = 'rgb(59, 130, 246)'
}) => {
  const chartData = {
    labels: data.map(item => item.age),
    datasets: [
      {
        label: `${tableName} - Taxa de Mortalidade (qx)`,
        data: data.map(item => item.qx),
        borderColor: color,
        backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
        borderWidth: 2,
        pointRadius: 1,
        pointHoverRadius: 4,
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      // Garantir que não haja rótulos do datalabels também neste gráfico
      datalabels: {
        display: false,
      },
      title: {
        display: true,
        text: `Taxa de Mortalidade - ${tableName}`,
        font: {
          size: 16,
          weight: 'bold' as const,
        },
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            return `Idade ${context.label}: ${(context.parsed.y * 1000).toFixed(3)}‰`;
          },
        },
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Idade',
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Taxa de Mortalidade (qx)',
        },
        ticks: {
          callback: function(value: any) {
            return (value * 1000).toFixed(1) + '‰';
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
    <div className="w-full h-96 p-4 bg-white">
      <Line data={chartData} options={options} />
    </div>
  );
};

export default MortalityRateChart;
