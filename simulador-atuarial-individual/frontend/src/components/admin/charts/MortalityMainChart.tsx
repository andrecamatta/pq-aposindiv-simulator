import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface MortalityData {
  age: number;
  qx: number;
}

interface MortalityMainChartProps {
  data: MortalityData[];
  tableName: string;
  color?: string;
  showLogScale?: boolean;
}

const MortalityMainChart: React.FC<MortalityMainChartProps> = ({
  data,
  tableName,
  color = 'rgb(59, 130, 246)',
  showLogScale = true
}) => {
  const chartData = {
    labels: data.map(item => item.age),
    datasets: [
      {
        label: `${tableName}`,
        data: data.map(item => item.qx),
        borderColor: color,
        backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
        borderWidth: 2.5,
        pointRadius: 0,
        pointHoverRadius: 0, // Remover hover points
        pointHoverBorderWidth: 0,
        tension: 0.2,
        fill: true,
        fillBetween: 'origin',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 14,
            weight: '500' as const,
          },
        },
      },
      // Remover rótulos/annotations do plugin chartjs-plugin-datalabels
      datalabels: {
        display: false,
      },
      title: {
        display: true,
        text: `Curva de Mortalidade - ${tableName}`,
        font: {
          size: 18,
          weight: 'bold' as const,
        },
        padding: {
          top: 10,
          bottom: 30,
        },
      },
      tooltip: {
        enabled: false, // Desabilitar tooltips completamente
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Idade (anos)',
          font: {
            size: 14,
            weight: '600' as const,
          },
          padding: {
            top: 10,
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
          lineWidth: 1,
        },
        ticks: {
          font: {
            size: 12,
          },
          maxTicksLimit: 8, // Reduzir ticks no eixo X também
        },
      },
      y: {
        type: showLogScale ? 'logarithmic' as const : 'linear' as const,
        display: true,
        title: {
          display: true,
          text: `Taxa de Mortalidade (qx) - ${showLogScale ? 'Escala Log' : 'Escala Linear'}`,
          font: {
            size: 14,
            weight: '600' as const,
          },
          padding: {
            bottom: 10,
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
          lineWidth: 1,
        },
        ticks: {
          display: false, // Desabilitar ticks completamente para eliminar annotations
        },
        min: showLogScale ? 0.0001 : undefined, // Evitar log(0)
      },
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
    animation: {
      duration: 750,
      easing: 'easeInOutQuart' as const,
    },
    elements: {
      point: {
        hoverBackgroundColor: color,
        hoverBorderColor: 'white',
        radius: 0, // Garantir que pontos não sejam visíveis
        hoverRadius: 0,
      },
    },
  };

  return (
    <div className="w-full h-[500px] bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="p-4 h-full">
        <Line data={chartData} options={options} />
      </div>
      
      {/* Controls */}
      <div className="px-4 pb-3 border-t border-gray-100 bg-gray-50/50">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center space-x-4">
            <span className="flex items-center">
              <div 
                className="w-3 h-0.5 mr-2 rounded"
                style={{ backgroundColor: color }}
              />
              {data.length} pontos de idade
            </span>
            <span>
              Faixa: {Math.min(...data.map(d => d.age))} - {Math.max(...data.map(d => d.age))} anos
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <span>Escala: {showLogScale ? 'Logarítmica' : 'Linear'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MortalityMainChart;
