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
  chartType?: 'mortality' | 'survival' | 'life_expectancy' | 'deaths';
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
    if (!data || data.length === 0) return [];
    
    // Ordenar dados por idade para garantir sequência correta
    const sortedData = [...data].sort((a, b) => a.age - b.age);
    
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

  // Calcular expectativa de vida remanescente (êx)
  const calculateLifeExpectancyData = () => {
    if (!data || data.length === 0) return [];
    
    const sortedData = [...data].sort((a, b) => a.age - b.age);
    const survivalData = calculateSurvivalData();
    
    return sortedData.map((item, index) => {
      let totalLifeYears = 0;
      const currentSurvivors = survivalData[index];
      
      if (currentSurvivors > 0) {
        // Somar anos de vida restantes para todas as idades futuras
        for (let futureIndex = index; futureIndex < survivalData.length; futureIndex++) {
          totalLifeYears += survivalData[futureIndex] / currentSurvivors;
        }
      }
      
      return Math.max(0, totalLifeYears);
    });
  };

  // Calcular número de mortes por idade (dx)
  const calculateDeathsData = () => {
    if (!data || data.length === 0) return [];
    
    const sortedData = [...data].sort((a, b) => a.age - b.age);
    const survivalData = calculateSurvivalData();
    
    return sortedData.map((item, index) => {
      const qx = Math.min(Math.max(item.qx || 0, 0), 1);
      const survivors = survivalData[index];
      return survivors * qx;
    });
  };

  
  const chartValues = () => {
    switch (chartType) {
      case 'survival':
        return calculateSurvivalData();
      case 'life_expectancy':
        return calculateLifeExpectancyData();
      case 'deaths':
        return calculateDeathsData();
      default: // 'mortality'
        return data.map(item => item.qx);
    }
  };
  const getChartLabel = () => {
    switch (chartType) {
      case 'survival':
        return 'Sobrevivência';
      case 'life_expectancy':
        return 'Expectativa de Vida';
      case 'deaths':
        return 'Número de Mortes';
      default:
        return 'Mortalidade';
    }
  };

  const getChartTitle = () => {
    switch (chartType) {
      case 'survival':
        return 'Curva de Sobrevivência';
      case 'life_expectancy':
        return 'Expectativa de Vida Remanescente';
      case 'deaths':
        return 'Distribuição de Mortes por Idade';
      default:
        return 'Curva de Mortalidade';
    }
  };

  const getYAxisTitle = () => {
    switch (chartType) {
      case 'survival':
        return 'Número de Sobreviventes';
      case 'life_expectancy':
        return 'Anos de Vida Restantes (êx)';
      case 'deaths':
        return `Número de Mortes (dx) - ${showLogScale ? 'Escala Log' : 'Escala Linear'}`;
      default:
        return `Taxa de Mortalidade (%) - ${showLogScale ? 'Escala Log' : 'Escala Linear'}`;
    }
  };

  const chartData = {
    labels: data.map(item => item.age),
    datasets: [
      {
        label: `${tableName} - ${getChartLabel()}`,
        data: chartValues(),
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
            weight: 500,
          },
        },
      },
      // Remover rótulos/annotations do plugin chartjs-plugin-datalabels
      datalabels: {
        display: false,
      },
      title: {
        display: true,
        text: `${getChartTitle()} - ${tableName}`,
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
            switch (chartType) {
              case 'survival':
                return `Sobreviventes: ${value.toLocaleString('pt-BR')}`;
              case 'life_expectancy':
                return `Expectativa de Vida: ${value.toLocaleString('pt-BR', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })} anos`;
              case 'deaths':
                return `Mortes: ${value.toLocaleString('pt-BR', {
                  maximumFractionDigits: 0
                })}`;
              default:
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
        type: (showLogScale && (chartType === 'mortality' || chartType === 'deaths')) ? 'logarithmic' as const : 'linear' as const,
        display: true,
        title: {
          display: true,
          text: getYAxisTitle(),
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
              return showLogScale ? 1 : 0;
            default:
              return showLogScale ? 0.0001 : 0;
          }
        })(),
        max: (() => {
          switch (chartType) {
            case 'survival':
              return 100000;
            case 'life_expectancy':
              return undefined; // Deixar automático
            case 'deaths':
              return undefined; // Deixar automático
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
      <div className="px-4 pb-3 border-t border-gray-100">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center space-x-4">
            <span className="flex items-center">
              <div 
                className="w-3 h-0.5 mr-2 rounded"
                style={{ backgroundColor: color }}
              />
              {tableName}
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
