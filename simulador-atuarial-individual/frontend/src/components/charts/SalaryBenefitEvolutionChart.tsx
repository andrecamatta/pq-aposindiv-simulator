import React from 'react';
import { Icon } from '../../design-system/components/Icon';
import { Bar } from 'react-chartjs-2';
import type { SimulatorResults, SimulatorState } from '../../types/simulator.types';
import { getZeroLineGridConfig } from '../../utils/chartSetup';
import { formatCurrencyBR } from '../../utils/formatBR';

interface SalaryBenefitEvolutionChartProps {
  results: SimulatorResults;
  state: SimulatorState;
}

const SalaryBenefitEvolutionChart: React.FC<SalaryBenefitEvolutionChartProps> = ({ results, state }) => {
  // Detectar tipo de plano e usar dados apropriados
  const isCD = state.plan_type === 'CD';

  // Para CD: usar projection_years, projected_salaries, projected_benefits
  // Para BD: usar projection_ages, projected_salaries_by_age, projected_benefits_by_age
  const hasValidData = isCD
    ? (results?.projection_years && Array.isArray(results.projection_years))
    : (results?.projection_ages && Array.isArray(results.projection_ages));

  if (!results || !hasValidData) {
    return (
      <div className="h-[26rem] flex items-center justify-center">
        <div className="text-center">
          <Icon name="trending-up" size="xl" className="text-gray-400 mb-4" />
          <p className="text-gray-500">Dados insuficientes para gerar o gráfico</p>
          <p className="text-sm text-gray-400">Configure os parâmetros e execute a simulação</p>
        </div>
      </div>
    );
  }

  // Usar dados apropriados baseado no tipo de plano
  const ageLabels = isCD
    ? results.projection_years?.map((year, idx) => (state.age || 30) + idx) || []
    : results.projection_ages || [];

  const salaryData = isCD
    ? results.projected_salaries || []
    : results.projected_salaries_by_age || [];

  const benefitData = isCD
    ? results.projected_benefits || []
    : results.projected_benefits_by_age || [];

  // Identificar o ponto de aposentadoria
  const retirementAge = state.retirement_age || 65;

  const data = {
    labels: ageLabels,
    datasets: [
      {
        label: 'Salário',
        data: ageLabels.map((age, idx) =>
          age < retirementAge ? (salaryData[idx] || 0) : 0
        ),
        backgroundColor: 'rgba(59, 130, 246, 0.8)', // blue-500
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1,
      },
      {
        label: 'Benefício',
        data: ageLabels.map((age, idx) =>
          age >= retirementAge ? (benefitData[idx] || 0) : 0
        ),
        backgroundColor: 'rgba(16, 185, 129, 0.8)', // emerald-500
        borderColor: 'rgb(16, 185, 129)',
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        align: 'end' as const,
        labels: {
          boxWidth: 12,
          boxHeight: 12,
          padding: 15,
          font: {
            size: 12,
          },
          usePointStyle: true,
          pointStyle: 'circle',
        },
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: '#374151',
        borderWidth: 1,
        titleFont: {
          size: 13,
          weight: 600,
        },
        bodyFont: {
          size: 12,
        },
        padding: 12,
        displayColors: false,
        callbacks: {
          title: (tooltipItems: any) => {
            const age = tooltipItems[0].label;
            const isRetired = age >= retirementAge;
            const phase = isRetired ? 'Aposentadoria' : 'Fase Ativa';
            return `Idade: ${age} anos (${phase})`;
          },
          label: (context: any) => {
            const value = context.parsed.y;
            if (value === null || value === undefined) return '';

            // Usar datasetIndex para identificar a série: 0 = Salário, 1 = Benefício
            const label = context.datasetIndex === 0 ? 'Salário Mensal' : 'Benefício Mensal';
            return `${label}: ${formatCurrencyBR(value, 2)}`;
          },
          afterBody: (tooltipItems: any) => {
            const age = tooltipItems[0].label;
            const isRetired = age >= retirementAge;

            if (age == retirementAge) {
              return ['', 'Marca o início da aposentadoria'];
            }

            return [];
          },
        },
      },
      datalabels: {
        display: false,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Idade (anos)',
          font: {
            size: 12,
            weight: 500,
          },
          color: '#6b7280',
        },
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 11,
          },
          color: '#6b7280',
          maxTicksLimit: 10,
        },
      },
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Valor (R$)',
          font: {
            size: 12,
            weight: 500,
          },
          color: '#6b7280',
        },
        grid: {
          display: true,
          color: 'rgba(0, 0, 0, 0.05)',
          lineWidth: 0.5,
        },
        ticks: {
          font: {
            size: 11,
          },
          color: '#6b7280',
          callback: function(value: any) {
            return formatCurrencyBR(value, 0);
          },
        },
      },
    },
  };


  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">
          Evolução Salarial e Benefícios (Valores Mensais)
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          {isCD
            ? 'Progressão do salário mensal durante a fase de acumulação, seguida pelos benefícios mensais na aposentadoria'
            : 'Progressão do salário mensal durante a fase ativa e benefícios mensais na aposentadoria'
          }
        </p>
      </div>


      {/* Gráfico */}
      <div className="h-[20rem] relative">
        <Bar data={data} options={options} />
      </div>

    </div>
  );
};

export default SalaryBenefitEvolutionChart;