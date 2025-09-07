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
  chartType?: 'mortality' | 'survival';
}

const MortalityMainChart: React.FC<MortalityMainChartProps> = ({
  data,
  tableName,
  color = 'rgb(59, 130, 246)',
  showLogScale = true,
  chartType = 'mortality'
}) => {
  // Calcular curva de sobrevivência se necessário
  const calculateSurvivalData = () => {
    let survivors = 100000; // radix padrão
    return data.map(item => {
      const lx = survivors;
      survivors = survivors * (1 - Math.min(Math.max(item.qx, 0), 1));
      return lx;
    });
  };
  
  const chartValues = chartType === 'survival' ? calculateSurvivalData() : data.map(item => item.qx);
  const chartData = {
    labels: data.map(item => item.age),
    datasets: [
      {
        label: `${tableName} - ${chartType === 'survival' ? 'Sobrevivência' : 'Mortalidade'}`,
        data: chartValues,
        borderColor: color,
        backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
        borderWidth: 2.5,
        pointRadius: 0,
        pointHoverRadius: 5, // Mostrar pontos no hover
        pointHoverBorderWidth: 2,
        pointHoverBackgroundColor: color,
        pointHoverBorderColor: 'white',
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
        text: `${chartType === 'survival' ? 'Curva de Sobrevivência' : 'Curva de Mortalidade'} - ${tableName}`,
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
        enabled: true,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        padding: 12,
        displayColors: false,
        cornerRadius: 8,
        titleFont: {
          size: 14,
          weight: 'bold' as const,
        },
        bodyFont: {
          size: 13,
        },
        callbacks: {
          title: (tooltipItems: any) => {
            return `Idade: ${tooltipItems[0].label} anos`;
          },
          label: (tooltipItem: any) => {
            const value = tooltipItem.raw;
            if (chartType === 'survival') {
              return `Sobreviventes: ${value.toLocaleString('pt-BR')}`;
            } else {
              return `Taxa de Mortalidade: ${(value * 100).toLocaleString('pt-BR', {
                minimumFractionDigits: 3,
                maximumFractionDigits: 3
              })}%`;
            }
          },
        },
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
        type: (showLogScale && chartType === 'mortality') ? 'logarithmic' as const : 'linear' as const,
        display: true,
        title: {
          display: true,
          text: chartType === 'survival' 
            ? 'Número de Sobreviventes' 
            : `Taxa de Mortalidade (%) - ${showLogScale ? 'Escala Log' : 'Escala Linear'}`,
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
          display: true,
          callback: function(value: any) {
            if (typeof value === 'number') {
              if (chartType === 'survival') {
                return value.toLocaleString('pt-BR');
              } else {
                return (value * 100).toLocaleString('pt-BR', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                }) + '%';
              }
            }
            return value;
          },
          font: {
            size: 10,
          },
          maxTicksLimit: 6,
        },
        min: (showLogScale && chartType === 'mortality') ? 0.0001 : 0,
        max: chartType === 'survival' ? 100000 : undefined,
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
        hoverBorderWidth: 2,
        radius: 0, // Pontos normalmente invisíveis
        hoverRadius: 5, // Pontos visíveis ao passar o mouse
        pointStyle: 'circle',
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
