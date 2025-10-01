import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartDataLabels
);

export const getZeroLineGridConfig = () => ({
  display: true,
  color: function(context: any) {
    if (context.tick.value === 0) {
      return '#000000'; // Linha preta no zero
    }
    return '#F3F4F6'; // Linha cinza padrão
  },
  lineWidth: function(context: any) {
    if (context.tick.value === 0) {
      return 3; // Linha mais grossa no zero
    }
    return 1; // Espessura padrão
  },
});

export const getCleanGridConfig = () => ({
  display: true,
  color: function(context: any) {
    if (context.tick.value === 0) {
      return '#374151'; // Linha mais escura no zero
    }
    return '#F8F9FA'; // Linha muito sutil para o resto
  },
  lineWidth: function(context: any) {
    if (context.tick.value === 0) {
      return 2; // Linha do zero um pouco mais grossa
    }
    return 0.5; // Linhas muito finas para o resto
  },
  drawTicks: false, // Remove os pequenos traços nos eixos
});

export const getBaseChartOptions = () => ({
  responsive: true,
  maintainAspectRatio: false,
  layout: {
    padding: {
      top: 40,
      bottom: 10,
      left: 10,
      right: 10,
    },
  },
  plugins: {
    legend: {
      display: false,
    },
    datalabels: {
      display: false,
    },
  },
  interaction: {
    intersect: false,
    mode: 'index' as const,
  },
});

export const getBarChartOptions = (yAxisTitle = 'Valores (R$)') => ({
  ...getBaseChartOptions(),
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
      },
      title: {
        display: true,
        text: yAxisTitle,
        font: {
          size: 12,
          weight: 'bold' as const,
        },
        color: '#374151',
      },
    },
  },
});

export const getLineChartOptions = (xAxisTitle = 'Idade (anos)', yAxisTitle = 'Valores (R$)') => ({
  ...getBaseChartOptions(),
  plugins: {
    ...getBaseChartOptions().plugins,
    legend: {
      position: 'top' as const,
      labels: {
        usePointStyle: true,
        padding: 20,
        font: {
          size: 12,
        },
      },
    },
  },
  scales: {
    x: {
      title: {
        display: true,
        text: xAxisTitle,
      },
      grid: {
        display: false,
      },
      ticks: {
        display: true,
        font: {
          size: 11,
        },
        color: '#6B7280',
      },
    },
    y: {
      title: {
        display: true,
        text: yAxisTitle,
      },
      grid: getZeroLineGridConfig(),
      ticks: {
        display: true,
        font: {
          size: 11,
        },
        color: '#6B7280',
      },
    },
  },
});

export const getDoughnutChartOptions = () => ({
  ...getBaseChartOptions(),
  plugins: {
    ...getBaseChartOptions().plugins,
    legend: {
      position: 'right' as const,
      labels: {
        usePointStyle: true,
        padding: 20,
        font: {
          size: 12,
        },
      },
    },
  },
  cutout: '60%',
});

export default ChartJS;