import React from 'react';
import { Icon } from '../../design-system/components/Icon';
import { Line } from 'react-chartjs-2';
import type { SimulatorResults, SimulatorState } from '../../types/simulator.types';
import { formatCurrencyBR, formatSimplePercentageBR } from '../../utils/formatBR';

interface CDContributionImpactChartProps {
  results: SimulatorResults;
  state: SimulatorState;
}

const CDContributionImpactChart: React.FC<CDContributionImpactChartProps> = ({ results, state }) => {
  // Verificações de segurança
  if (!results || !state) {
    return (
      <div className="h-[32rem] flex items-center justify-center">
        <div className="text-center">
          <Icon name="bar-chart" size="xl" className="text-gray-400 mb-4" />
          <p className="text-gray-500">Dados insuficientes para gerar o gráfico</p>
          <p className="text-sm text-gray-400">Configure os parâmetros e execute a simulação</p>
        </div>
      </div>
    );
  }

  // Taxas de contribuição para comparação
  const contributionRates = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20];
  const currentRate = (state.contribution_rate || 0) / 100;
  
  // Parâmetros base para cálculos
  const currentAge = state.age || 30;
  const retirementAge = state.retirement_age || 65;
  const yearsToRetirement = retirementAge - currentAge;
  const monthlySalary = state.salary || 0;
  const accumulationRate = (state.accumulation_rate || 0.065);
  const conversionRate = (state.conversion_rate || 0.045);
  
  // Calcular projeções para cada taxa de contribuição
  const calculateProjection = (contribRate: number) => {
    const monthlyContrib = monthlySalary * contribRate;
    const monthlyRate = accumulationRate / 12;
    const totalMonths = yearsToRetirement * 12;
    const initialBalance = state.initial_balance || 0;
    
    // Simular acumulação mês a mês (como no backend)
    let balance = initialBalance;
    let totalContributions = 0;
    
    for (let month = 0; month < totalMonths; month++) {
      // Capitalizar saldo existente
      balance *= (1 + monthlyRate);
      
      // Aplicar taxa administrativa (1% ao ano = ~0.083% ao mês)
      const adminFeeMonthly = (state.admin_fee_annual || 1) / 100 / 12;
      balance *= (1 - adminFeeMonthly);
      
      // Adicionar contribuição
      balance += monthlyContrib;
      totalContributions += monthlyContrib;
    }
    
    const finalBalance = balance;
    
    // Calcular renda mensal usando lógica similar ao backend
    // Para vitalícia: usar aproximação baseada na expectativa de vida
    let monthlyIncome: number;
    
    if (state.cd_conversion_mode === 'ACTUARIAL') {
      // Aproximação para vitalícia: ~25 anos de expectativa após aposentadoria
      const expectedLifeYears = 25;
      const expectedLifeMonths = expectedLifeYears * 12;
      const conversionMonthlyRate = conversionRate / 12;
      
      // Fórmula de anuidade vitalícia aproximada
      const annuityFactor = expectedLifeMonths > 0 ? 
        ((1 - Math.pow(1 + conversionMonthlyRate, -expectedLifeMonths)) / conversionMonthlyRate) : 
        expectedLifeMonths;
      
      monthlyIncome = annuityFactor > 0 ? finalBalance / annuityFactor : 0;
    } else {
      // Para prazo determinado (simplificado)
      const years = 20; // Assumir 20 anos como padrão
      const months = years * 12;
      const conversionMonthlyRate = conversionRate / 12;
      
      const annuityFactor = months > 0 ? 
        ((1 - Math.pow(1 + conversionMonthlyRate, -months)) / conversionMonthlyRate) : 
        months;
      
      monthlyIncome = annuityFactor > 0 ? finalBalance / annuityFactor : 0;
    }
    
    return {
      finalBalance,
      monthlyIncome,
      annualIncome: monthlyIncome * 12,
      totalContributions
    };
  };
  
  // Dados para cada taxa de contribuição
  const projectionsData = contributionRates.map(rate => ({
    rate,
    ...calculateProjection(rate)
  }));
  
  // Labels das taxas
  const labels = contributionRates.map(rate => `${formatSimplePercentageBR(rate * 100, 0)}`);
  
  // Encontrar taxa necessária para o benefício alvo
  const targetBenefit = state.target_benefit || 0;
  const targetRate = targetBenefit > 0 ? contributionRates.find(rate => 
    calculateProjection(rate).monthlyIncome >= targetBenefit
  ) : null;

  const data = {
    labels,
    datasets: [
      {
        label: 'Saldo Acumulado',
        data: projectionsData.map(p => p.finalBalance),
        borderColor: '#93C5FD',
        backgroundColor: 'rgba(147, 197, 253, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: (context: any) => {
          const rate = contributionRates[context.dataIndex];
          return Math.abs(rate - currentRate) < 0.001 ? 8 : 4;
        },
        pointBackgroundColor: (context: any) => {
          const rate = contributionRates[context.dataIndex];
          return Math.abs(rate - currentRate) < 0.001 ? '#60A5FA' : '#93C5FD';
        },
        yAxisID: 'y',
      },
      {
        label: 'Renda Mensal CD',
        data: projectionsData.map(p => p.monthlyIncome),
        borderColor: '#6EE7B7',
        backgroundColor: 'rgba(110, 231, 183, 0.1)',
        tension: 0.4,
        fill: false,
        pointRadius: (context: any) => {
          const rate = contributionRates[context.dataIndex];
          return Math.abs(rate - currentRate) < 0.001 ? 8 : 4;
        },
        pointBackgroundColor: (context: any) => {
          const rate = contributionRates[context.dataIndex];
          return Math.abs(rate - currentRate) < 0.001 ? '#34D399' : '#6EE7B7';
        },
        yAxisID: 'y1',
      },
      {
        label: 'Meta de Benefício',
        data: targetBenefit > 0 ? new Array(labels.length).fill(targetBenefit) : [],
        borderColor: '#F87171',
        backgroundColor: 'transparent',
        borderDash: [8, 4],
        tension: 0,
        fill: false,
        pointRadius: 0,
        yAxisID: 'y1',
      }
    ],
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
            size: 12,
          },
          filter: (legendItem: any) => {
            return targetBenefit > 0 || legendItem.text !== 'Meta de Benefício';
          }
        },
      },
      tooltip: {
        callbacks: {
          title: function(tooltipItems: any[]) {
            const dataIndex = tooltipItems[0]?.dataIndex;
            const rate = contributionRates[dataIndex];
            const isCurrentRate = Math.abs(rate - currentRate) < 0.001;
            return `Contribuição ${formatSimplePercentageBR(rate * 100, 1)}${isCurrentRate ? ' (Atual)' : ''}`;
          },
          label: function(context: any) {
            const value = context.parsed.y;
            if (context.dataset.label === 'Meta de Benefício') {
              return `Meta: ${formatCurrencyBR(value, 0)}`;
            }
            return `${context.dataset.label}: ${formatCurrencyBR(value, 0)}`;
          },
          afterBody: function(tooltipItems: any[]) {
            const dataIndex = tooltipItems[0]?.dataIndex;
            const projection = projectionsData[dataIndex];
            const rate = contributionRates[dataIndex];
            
            return [
              `Taxa de contribuição: ${formatSimplePercentageBR(rate * 100, 1)} do salário`,
              `Total contribuído: ${formatCurrencyBR(projection.totalContributions, 0)}`,
              `Rendimento líquido: ${formatCurrencyBR(projection.finalBalance - projection.totalContributions, 0)}`
            ];
          }
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
          text: 'Taxa de Contribuição (%)',
        },
        grid: {
          display: false,
        },
        ticks: {
          font: {
            size: 11,
          },
          color: '#6B7280',
        },
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Saldo Acumulado (R$)',
          color: '#93C5FD',
        },
        ticks: {
          font: {
            size: 11,
          },
          color: '#93C5FD',
          callback: function(value: any) {
            return formatCurrencyBR(value, 0);
          },
        },
        grid: {
          display: true,
          color: 'rgba(59, 130, 246, 0.1)',
        },
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Renda Mensal (R$)',
          color: '#6EE7B7',
        },
        ticks: {
          font: {
            size: 11,
          },
          color: '#6EE7B7',
          callback: function(value: any) {
            return formatCurrencyBR(value, 0);
          },
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index' as const,
    },
  };

  // Encontrar dados da taxa atual
  const currentProjection = calculateProjection(currentRate);

  return (
    <div className="h-[32rem]">
      {/* Título */}
      <div className="mb-4 px-1">
        <h3 className="text-lg font-semibold text-gray-900">
          Impacto da Taxa de Contribuição
        </h3>
      </div>
      
      {/* Gráfico */}
      <div className="h-[24rem]">
        <Line data={data} options={options} />
      </div>
    </div>
  );
};

export default CDContributionImpactChart;