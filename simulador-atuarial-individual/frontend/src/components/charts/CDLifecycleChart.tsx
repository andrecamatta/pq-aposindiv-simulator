import React from 'react';
import { Icon } from '../../design-system/components/Icon';
import { Line } from 'react-chartjs-2';
import type { SimulatorResults, SimulatorState } from '../../types/simulator.types';
import { getZeroLineGridConfig } from '../../utils/chartSetup';
import { formatCurrencyBR } from '../../utils/formatBR';

interface CDLifecycleChartProps {
  results: SimulatorResults;
  state: SimulatorState;
}

const CDLifecycleChart: React.FC<CDLifecycleChartProps> = ({ results, state }) => {
  // Verificações de segurança
  if (!results || !results.projection_years || !Array.isArray(results.projection_years)) {
    return (
      <div className="h-[32rem] flex items-center justify-center">
        <div className="text-center">
          <Icon name="trending-up" size="xl" className="text-gray-400 mb-4" />
          <p className="text-gray-500">Dados insuficientes para gerar o gráfico</p>
          <p className="text-sm text-gray-400">Configure os parâmetros e execute a simulação</p>
        </div>
      </div>
    );
  }

  // Calcular labels de idade baseadas na idade atual
  const ageLabels = results.projection_years.map(year => state.age + year);
  
  // Identificar o ponto de aposentadoria
  const retirementAge = state.retirement_age || 65;
  const retirementIndex = ageLabels.findIndex(age => age >= retirementAge);
  
  // Separar dados em fases de acumulação e aposentadoria
  const accumulationAges = ageLabels.slice(0, retirementIndex + 1);
  const retirementAges = ageLabels.slice(retirementIndex);
  
  const accumulationBalances = (results.accumulated_reserves || []).slice(0, retirementIndex + 1);
  const retirementBalances = (results.accumulated_reserves || []).slice(retirementIndex);
  
  // Calcular pico de saldo e data de exaustão estimada
  const peakBalance = Math.max(...(results.accumulated_reserves || []));
  
  // Para planos CD, o pico sempre ocorre na idade de aposentadoria
  // Isso garante consistência entre métricas e visualização do gráfico
  const peakAge = retirementAge;
  
  // Calcular duração baseada na modalidade de conversão
  let benefitDurationYears: number | null = null;
  let exhaustionAge: number | null = null;
  
  if (state.cd_conversion_mode) {
    // Para modalidades com prazo determinado, usar o prazo exato
    const conversionModeYears: Record<string, number> = {
      'CERTAIN_5Y': 5,
      'CERTAIN_10Y': 10,
      'CERTAIN_15Y': 15,
      'CERTAIN_20Y': 20
    };
    
    if (conversionModeYears[state.cd_conversion_mode]) {
      benefitDurationYears = conversionModeYears[state.cd_conversion_mode];
      exhaustionAge = retirementAge + benefitDurationYears;
    }
  }
  
  // Se não foi determinado pela modalidade, calcular pela exaustão do saldo (para modo vitalício)
  if (!exhaustionAge) {
    const exhaustionThreshold = peakBalance * 0.1;
    const exhaustionIndex = results.accumulated_reserves?.findIndex((balance, index) => 
      index > retirementIndex && balance < exhaustionThreshold
    );
    exhaustionAge = exhaustionIndex && exhaustionIndex > 0 ? ageLabels[exhaustionIndex] : null;
  }

  // Calcular projeção alternativa com benefício desejado (para comparação de suficiência)
  const calculateAlternativeProjection = () => {
    // Verificar se deve mostrar comparação
    const showComparison = state.benefit_target_mode === 'VALUE' && 
                           state.target_benefit && 
                           state.target_benefit > 0 && 
                           results.monthly_income_cd && 
                           Math.abs(state.target_benefit - results.monthly_income_cd) > 100; // Diferença significativa
    
    if (!showComparison) return null;

    // Configurações para cálculo alternativo
    const targetBenefit = state.target_benefit || 0;
    const conversionRateMonthly = (state.conversion_rate || 0.045) / 12; // Taxa de conversão mensal do estado
    const benefitMonthsPerYear = state.benefit_months_per_year || 13;
    
    // Simular evolução do saldo com benefício desejado
    const alternativeBalances: number[] = [];
    let remainingBalance = peakBalance; // Começar com o pico (saldo na aposentadoria)
    
    // Preencher fase de acumulação com nulls
    for (let i = 0; i <= retirementIndex; i++) {
      alternativeBalances.push(null as any);
    }
    
    // Simular fase de aposentadoria mês a mês
    let alternativeExhaustionAge: number | null = null;
    let monthsCount = 0;
    
    for (let i = retirementIndex; i < ageLabels.length; i++) {
      let monthlyBalance = remainingBalance;
      
      // Simular 12 meses para este ano
      for (let month = 0; month < 12; month++) {
        const currentMonthInYear = month;
        let monthlyPayment = targetBenefit; // Pagamento base mensal
        
        // Aplicar pagamentos extras baseado na configuração do backend
        const extraPayments = benefitMonthsPerYear - 12;
        if (extraPayments > 0) {
          if (currentMonthInYear === 11) { // Dezembro - 13º
            if (extraPayments >= 1) {
              monthlyPayment += targetBenefit;
            }
          }
          if (currentMonthInYear === 0 && monthsCount > 0) { // Janeiro - 14º
            if (extraPayments >= 2) {
              monthlyPayment += targetBenefit;
            }
          }
        }
        
        // Descontar pagamento do saldo
        monthlyBalance -= monthlyPayment;
        
        // Capitalizar saldo restante
        monthlyBalance *= (1 + conversionRateMonthly);
        
        // Garantir que não fique negativo
        monthlyBalance = Math.max(0, monthlyBalance);
        
        monthsCount++;
        
        // Se saldo zerou, parar
        if (monthlyBalance <= 0) {
          break;
        }
      }
      
      remainingBalance = monthlyBalance;
      
      alternativeBalances.push(remainingBalance);
      
      // Detectar ponto de exaustão
      if (remainingBalance <= peakBalance * 0.05 && !alternativeExhaustionAge) { // 5% do pico
        alternativeExhaustionAge = ageLabels[i];
      }
      
      // Parar simulação se saldo zerou
      if (remainingBalance <= 0) {
        alternativeExhaustionAge = ageLabels[i];
        // Preencher resto com zeros
        for (let j = i + 1; j < ageLabels.length; j++) {
          alternativeBalances.push(0);
        }
        break;
      }
    }
    
    return {
      balances: alternativeBalances,
      exhaustionAge: alternativeExhaustionAge,
      targetBenefit
    };
  };

  const alternativeProjection = calculateAlternativeProjection();

  // Construir datasets dinamicamente
  const datasets: any[] = [
    {
      label: 'Fase de Acumulação',
      data: accumulationBalances.concat(new Array(ageLabels.length - accumulationBalances.length).fill(null)),
      borderColor: '#6EE7B7',
      backgroundColor: 'rgba(110, 231, 183, 0.1)',
      tension: 0.4,
      fill: true,
      pointRadius: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === peakAge ? 6 : 2;
      },
      pointBackgroundColor: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === peakAge ? '#34D399' : '#6EE7B7';
      },
      segment: {
        borderColor: (ctx: any) => {
          const age = ageLabels[ctx.p0DataIndex];
          return age >= retirementAge ? 'transparent' : '#6EE7B7';
        }
      }
    },
    {
      label: alternativeProjection ? 'Cenário Atuarial' : 'Fase de Aposentadoria',
      data: new Array(retirementIndex).fill(null).concat(retirementBalances),
      borderColor: '#FCD34D',
      backgroundColor: 'rgba(252, 211, 77, 0.1)',
      tension: 0.4,
      fill: alternativeProjection ? false : true,
      pointRadius: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === exhaustionAge ? 6 : 2;
      },
      pointBackgroundColor: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === exhaustionAge ? '#F87171' : '#FCD34D';
      },
      segment: {
        borderColor: (ctx: any) => {
          const age = ageLabels[ctx.p0DataIndex];
          return age < retirementAge ? 'transparent' : '#FCD34D';
        }
      }
    }
  ];

  // Adicionar dataset de comparação se disponível
  if (alternativeProjection) {
    datasets.push({
      label: `Cenário Desejado (R$ ${formatCurrencyBR(alternativeProjection.targetBenefit, 0)})`,
      data: alternativeProjection.balances,
      borderColor: '#F87171',
      backgroundColor: 'rgba(248, 113, 113, 0.1)',
      tension: 0.4,
      fill: false,
      borderWidth: 2,
      borderDash: [5, 3],
      pointRadius: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === alternativeProjection.exhaustionAge ? 8 : 2;
      },
      pointBackgroundColor: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === alternativeProjection.exhaustionAge ? '#DC2626' : '#F87171';
      },
      pointBorderColor: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === alternativeProjection.exhaustionAge ? '#FFFFFF' : '#F87171';
      },
      pointBorderWidth: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === alternativeProjection.exhaustionAge ? 2 : 0;
      },
      segment: {
        borderColor: (ctx: any) => {
          const age = ageLabels[ctx.p0DataIndex];
          return age < retirementAge ? 'transparent' : '#F87171';
        }
      }
    });
  }

  // Adicionar linha de aposentadoria
  datasets.push({
    label: 'Linha de Aposentadoria',
    data: ageLabels.map(age => age === retirementAge ? peakBalance * 1.1 : null),
    borderColor: '#A78BFA',
    borderWidth: 2,
    borderDash: [8, 4],
    pointRadius: 0,
    fill: false,
    tension: 0,
  });

  const data = {
    labels: ageLabels,
    datasets: datasets,
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
            return legendItem.text !== 'Linha de Aposentadoria';
          }
        },
      },
      tooltip: {
        enabled: false,
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
          text: 'Saldo da Conta Individual (R$)',
        },
        grid: getZeroLineGridConfig(),
        ticks: {
          display: true,
          font: {
            size: 11,
          },
          color: '#6B7280',
          callback: function(value: any) {
            return formatCurrencyBR(value, 0);
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
    <div className="h-[32rem]">
      {/* Título */}
      <div className="flex items-center gap-2 mb-4 px-1">
        <h3 className="text-lg font-semibold text-gray-900">
          Evolução do Saldo CD - Ciclo de Vida Completo
        </h3>
      </div>
      
      {/* Gráfico */}
      <div className="h-[26rem]">
        <Line data={data} options={options} />
      </div>
    </div>
  );
};

export default CDLifecycleChart;