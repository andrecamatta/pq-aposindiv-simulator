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

interface MortalityTableData {
  name: string;
  data: Array<{ age: number; qx: number }>;
  color: string;
}

interface MortalityComparisonChartProps {
  tables: MortalityTableData[];
  title?: string;
  chartType?: 'mortality' | 'survival';
}

const colors = [
  'rgb(59, 130, 246)',   // blue
  'rgb(239, 68, 68)',    // red
  'rgb(34, 197, 94)',    // green
  'rgb(251, 191, 36)',   // yellow
  'rgb(168, 85, 247)',   // purple
  'rgb(236, 72, 153)',   // pink
  'rgb(20, 184, 166)',   // teal
  'rgb(249, 115, 22)',   // orange
];

const MortalityComparisonChart: React.FC<MortalityComparisonChartProps> = ({
  tables,
  title = 'Comparação de Tábuas de Mortalidade',
  chartType = 'mortality'
}) => {
  // Função para calcular sobrevivência
  const calculateSurvivalData = (mortalityData: Array<{ age: number; qx: number }>) => {
    let survivors = 100000; // radix padrão
    const survivalData: { [age: number]: number } = {};
    
    // Ordenar por idade
    const sortedData = [...mortalityData].sort((a, b) => a.age - b.age);
    
    sortedData.forEach(item => {
      survivalData[item.age] = survivors;
      survivors = survivors * (1 - Math.min(Math.max(item.qx, 0), 1));
    });
    
    return survivalData;
  };
  // Find common age range
  const allAges = tables.flatMap(table => table.data.map(item => item.age));
  const minAge = Math.min(...allAges);
  const maxAge = Math.max(...allAges);
  const ageRange = Array.from({ length: maxAge - minAge + 1 }, (_, i) => minAge + i);

  const chartData = {
    labels: ageRange,
    datasets: tables.map((table, index) => {
      const survivalData = chartType === 'survival' ? calculateSurvivalData(table.data) : null;
      
      return {
        label: table.name,
        data: ageRange.map(age => {
          const dataPoint = table.data.find(item => item.age === age);
          if (chartType === 'survival' && survivalData) {
            return survivalData[age] || null;
          }
          return dataPoint ? dataPoint.qx : null;
        }),
      borderColor: table.color || colors[index % colors.length],
      backgroundColor: (table.color || colors[index % colors.length]).replace('rgb', 'rgba').replace(')', ', 0.1)'),
      borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 5, // Mostrar pontos no hover
        pointHoverBorderWidth: 2,
        pointHoverBackgroundColor: table.color || colors[index % colors.length],
        pointHoverBorderColor: 'white',
        tension: 0.1,
        spanGaps: true,
      };
    }),
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
        text: title,
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
        displayColors: true,
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
            if (value === null) return null;
            
            if (chartType === 'survival') {
              return `${tooltipItem.dataset.label}: ${value.toLocaleString('pt-BR')} sobreviventes`;
            } else {
              return `${tooltipItem.dataset.label}: ${(value * 100).toLocaleString('pt-BR', {
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
        type: chartType === 'mortality' ? 'logarithmic' as const : 'linear' as const,
        display: true,
        title: {
          display: true,
          text: chartType === 'survival' 
            ? 'Número de Sobreviventes' 
            : 'Taxa de Mortalidade (%) - Escala Logarítmica',
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
        min: chartType === 'mortality' ? 0.0001 : 0,
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
  };

  return (
    <div className="w-full h-[600px] bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="p-6 h-full">
        <Line data={chartData} options={options} />
      </div>
      
      {/* Controls */}
      <div className="px-6 pb-4 border-t border-gray-100 bg-gray-50/50">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center space-x-6">
            {tables.map((table, index) => (
              <span key={table.name} className="flex items-center">
                <div 
                  className="w-3 h-0.5 mr-2 rounded"
                  style={{ backgroundColor: table.color || colors[index % colors.length] }}
                />
                {table.name} ({table.data.length} pontos)
              </span>
            ))}
          </div>
          <div className="flex items-center space-x-2">
            <span>Escala: {chartType === 'mortality' ? 'Logarítmica' : 'Linear'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MortalityComparisonChart;
