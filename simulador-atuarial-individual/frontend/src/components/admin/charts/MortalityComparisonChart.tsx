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
  chartType?: 'mortality' | 'survival' | 'life_expectancy' | 'deaths';
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
    if (!mortalityData || mortalityData.length === 0) return [];
    
    // Ordenar por idade
    const sortedData = [...mortalityData].sort((a, b) => a.age - b.age);
    
    let survivors = 100000; // radix padrão
    return sortedData.map(item => {
      const currentSurvivors = survivors;
      // Validar qx: deve estar entre 0 e 1
      const qx = Math.min(Math.max(item.qx || 0, 0), 1);
      // Aplicar mortalidade para próxima idade
      survivors = survivors * (1 - qx);
      return currentSurvivors;
    });
  };

  // Função para calcular expectativa de vida
  const calculateLifeExpectancyData = (mortalityData: Array<{ age: number; qx: number }>) => {
    if (!mortalityData || mortalityData.length === 0) return [];
    
    const sortedData = [...mortalityData].sort((a, b) => a.age - b.age);
    const survivalData = calculateSurvivalData(mortalityData);
    
    return sortedData.map((item, index) => {
      let totalLifeYears = 0;
      const currentSurvivors = survivalData[index];
      
      if (currentSurvivors > 0) {
        for (let futureIndex = index; futureIndex < survivalData.length; futureIndex++) {
          totalLifeYears += survivalData[futureIndex] / currentSurvivors;
        }
      }
      
      return Math.max(0, totalLifeYears);
    });
  };

  // Função para calcular número de mortes
  const calculateDeathsData = (mortalityData: Array<{ age: number; qx: number }>) => {
    if (!mortalityData || mortalityData.length === 0) return [];
    
    const sortedData = [...mortalityData].sort((a, b) => a.age - b.age);
    const survivalData = calculateSurvivalData(mortalityData);
    
    return sortedData.map((item, index) => {
      const qx = Math.min(Math.max(item.qx || 0, 0), 1);
      const survivors = survivalData[index];
      return survivors * qx;
    });
  };

  // Find common age range
  const allAges = tables.flatMap(table => table.data.map(item => item.age));
  const minAge = Math.min(...allAges);
  const maxAge = Math.max(...allAges);
  const ageRange = Array.from({ length: maxAge - minAge + 1 }, (_, i) => minAge + i);

  const chartData = {
    labels: ageRange,
    datasets: tables.map((table, index) => {
      let chartValues: (number | null)[];
      
      switch (chartType) {
        case 'survival':
          const survivalData = calculateSurvivalData(table.data);
          chartValues = ageRange.map(age => {
            const dataIndex = table.data.findIndex(item => item.age === age);
            return dataIndex !== -1 && survivalData[dataIndex] !== undefined ? survivalData[dataIndex] : null;
          });
          break;
        case 'life_expectancy':
          const lifeExpectancyData = calculateLifeExpectancyData(table.data);
          chartValues = ageRange.map(age => {
            const dataIndex = table.data.findIndex(item => item.age === age);
            return dataIndex !== -1 && lifeExpectancyData[dataIndex] !== undefined ? lifeExpectancyData[dataIndex] : null;
          });
          break;
        case 'deaths':
          const deathsData = calculateDeathsData(table.data);
          chartValues = ageRange.map(age => {
            const dataIndex = table.data.findIndex(item => item.age === age);
            return dataIndex !== -1 && deathsData[dataIndex] !== undefined ? deathsData[dataIndex] : null;
          });
          break;
        default: // 'mortality'
          chartValues = ageRange.map(age => {
            const dataPoint = table.data.find(item => item.age === age);
            return dataPoint ? dataPoint.qx : null;
          });
          break;
      }
      
      return {
        label: table.name,
        data: chartValues,
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
        backgroundColor: 'rgba(0, 0, 0, 0.95)',
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
            
            switch (chartType) {
              case 'survival':
                return `${tooltipItem.dataset.label}: ${value.toLocaleString('pt-BR')} sobreviventes`;
              case 'life_expectancy':
                return `${tooltipItem.dataset.label}: ${value.toLocaleString('pt-BR', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })} anos`;
              case 'deaths':
                return `${tooltipItem.dataset.label}: ${value.toLocaleString('pt-BR', {
                  maximumFractionDigits: 0
                })} mortes`;
              default:
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
        type: (chartType === 'mortality' || chartType === 'deaths') ? 'logarithmic' as const : 'linear' as const,
        display: true,
        title: {
          display: true,
          text: (() => {
            switch (chartType) {
              case 'survival':
                return 'Número de Sobreviventes';
              case 'life_expectancy':
                return 'Anos de Vida Restantes (êx)';
              case 'deaths':
                return 'Número de Mortes (dx) - Escala Logarítmica';
              default:
                return 'Taxa de Mortalidade (%) - Escala Logarítmica';
            }
          })(),
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
              switch (chartType) {
                case 'survival':
                  return value.toLocaleString('pt-BR');
                case 'life_expectancy':
                  return value.toLocaleString('pt-BR', {
                    minimumFractionDigits: 1,
                    maximumFractionDigits: 1
                  });
                case 'deaths':
                  return value.toLocaleString('pt-BR', {
                    maximumFractionDigits: 0
                  });
                default:
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
        min: (() => {
          switch (chartType) {
            case 'survival':
              return 0;
            case 'life_expectancy':
              return 0;
            case 'deaths':
              return 1; // Para escala log
            default:
              return 0.0001; // Para escala log da mortalidade
          }
        })(),
        max: (() => {
          switch (chartType) {
            case 'survival':
              return 100000;
            default:
              return undefined; // Deixar automático
          }
        })(),
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
      <div className="px-6 pb-4 border-t border-gray-100">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center space-x-6">
            {tables.map((table, index) => (
              <span key={table.name} className="flex items-center">
                <div 
                  className="w-3 h-0.5 mr-2 rounded"
                  style={{ backgroundColor: table.color || colors[index % colors.length] }}
                />
                {table.name}
              </span>
            ))}
          </div>
          <div className="flex items-center space-x-2">
            <span>Escala: {(chartType === 'mortality' || chartType === 'deaths') ? 'Logarítmica' : 'Linear'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MortalityComparisonChart;
