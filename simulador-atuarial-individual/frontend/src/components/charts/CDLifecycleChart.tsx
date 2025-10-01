import React from 'react';
import { Icon } from '../../design-system/components/Icon';
import { Line } from 'react-chartjs-2';
import type { SimulatorResults, SimulatorState } from '../../types/simulator.types';
import { getCleanGridConfig } from '../../utils/chartSetup';
import { formatCurrencyBR, formatCompactCurrencyBR } from '../../utils/formatBR';

// Constante para conversões de tempo calendário
const MONTHS_PER_YEAR = 12;

interface CDLifecycleChartProps {
  results: SimulatorResults;
  state: SimulatorState;
}

const CDLifecycleChart: React.FC<CDLifecycleChartProps> = ({ results, state }) => {

  // Função para obter informações da modalidade de conversão
  const getConversionModeInfo = (mode: string) => {
    const modeMap: Record<string, { label: string; icon: string }> = {
      'ACTUARIAL': { label: 'Renda Vitalícia Atuarial', icon: '🎯' },
      'ACTUARIAL_EQUIVALENT': { label: 'Equivalente Atuarial', icon: '⚖️' },
      'CERTAIN_5Y': { label: 'Prazo Certo - 5 Anos', icon: '⏰' },
      'CERTAIN_10Y': { label: 'Prazo Certo - 10 Anos', icon: '⏰' },
      'CERTAIN_15Y': { label: 'Prazo Certo - 15 Anos', icon: '⏰' },
      'CERTAIN_20Y': { label: 'Prazo Certo - 20 Anos', icon: '⏰' },
      'PERCENTAGE': { label: 'Percentual do Saldo', icon: '📊' },
      'PROGRAMMED': { label: 'Saque Programado', icon: '📉' }
    };

    return modeMap[mode] || { label: 'Renda Vitalícia Atuarial', icon: '🎯' };
  };

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

  // Usar dados do cenário atuarial se disponível (mais preciso após aplicar sugestões)
  // Caso contrário, usar accumulated_reserves como fallback
  const actuarialReserves = results.actuarial_scenario?.projections?.reserves || results.accumulated_reserves || [];

  const accumulationBalances = actuarialReserves.slice(0, retirementIndex + 1);
  const retirementBalances = actuarialReserves.slice(retirementIndex);
  
  // Calcular pico de saldo e data de exaustão estimada
  // Usar reservas do cenário atuarial para consistência
  const peakBalance = Math.max(...actuarialReserves);
  
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
    const exhaustionIndex = actuarialReserves.findIndex((balance, index) =>
      index > retirementIndex && balance < exhaustionThreshold
    );
    exhaustionAge = exhaustionIndex && exhaustionIndex > 0 ? ageLabels[exhaustionIndex] : null;
  }

  // Usar dados dos cenários do backend quando disponíveis (mais preciso)
  const getScenarioData = () => {
    // Se backend retornou cenários diferenciados, usar eles
    if (results.desired_scenario?.projections?.reserves) {
      // Calcular ponto de exaustão para cenário desejado
      const desiredReserves = results.desired_scenario.projections.reserves;
      const desiredExhaustionThreshold = Math.max(...desiredReserves) * 0.1;
      const desiredExhaustionIndex = desiredReserves.findIndex((balance, index) =>
        index > retirementIndex && balance < desiredExhaustionThreshold
      );
      const desiredExhaustionAge = desiredExhaustionIndex > 0 ? ageLabels[desiredExhaustionIndex] : null;

      return {
        actuarial: null, // Não precisamos, já estamos usando actuarialReserves
        desired: {
          balances: desiredReserves,
          monthly_income: results.desired_scenario.monthly_income,
          exhaustionAge: desiredExhaustionAge
        }
      };
    }

    // Fallback: calcular localmente (quando backend não retornou cenários)
    return calculateAlternativeProjection();
  };

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

    // Converter taxas anuais para mensais usando fórmula composta
    const conversionRateAnnual = state.cd_conversion_rate || 0.06;
    const conversionRateMonthly = Math.pow(1 + conversionRateAnnual, 1/12) - 1;

    const adminFeeAnnual = state.admin_fee_rate || 0.015;
    const adminFeeMonthly = Math.pow(1 + adminFeeAnnual, 1/12) - 1;

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
      for (let month = 0; month < MONTHS_PER_YEAR; month++) {
        const currentMonthInYear = month;
        let monthlyPayment = targetBenefit; // Pagamento base mensal

        // Aplicar pagamentos extras baseado na configuração do backend
        const extraPayments = benefitMonthsPerYear - MONTHS_PER_YEAR;
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

        // Capitalizar saldo restante com taxa de conversão
        monthlyBalance *= (1 + conversionRateMonthly);

        // Aplicar taxa administrativa (após capitalização)
        monthlyBalance *= (1 - adminFeeMonthly);

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
      actuarial: null,
      desired: {
        balances: alternativeBalances,
        exhaustionAge: alternativeExhaustionAge,
        monthly_income: targetBenefit
      }
    };
  };

  const scenarioData = getScenarioData();
  const alternativeProjection = scenarioData?.desired;

  // Função para gerar labels contextuais baseados na modalidade
  const getContextualLabels = () => {
    const conversionMode = state.cd_conversion_mode;
    const actuarialIncome = results.monthly_income_cd || 0;

    let accumulationLabel = 'Fase de Acumulação';
    let actuarialLabel = 'Cenário com Contribuição Atual';
    let desiredLabel = 'Cenário para Meta Desejada';

    // Personalizar labels baseado na modalidade
    if (conversionMode) {
      if (conversionMode.includes('CERTAIN')) {
        const years = conversionMode.split('_')[1].replace('Y', '');
        actuarialLabel = `Renda por ${years} Anos`;
      } else if (conversionMode === 'ACTUARIAL') {
        actuarialLabel = 'Renda Vitalícia Atuarial';
      } else if (conversionMode === 'PERCENTAGE') {
        actuarialLabel = 'Saque Percentual';
      } else if (conversionMode === 'PROGRAMMED') {
        actuarialLabel = 'Saque Programado';
      }
    }

    return { accumulationLabel, actuarialLabel, desiredLabel };
  };

  const { accumulationLabel, actuarialLabel, desiredLabel } = getContextualLabels();

  // Construir datasets dinamicamente com labels contextuais
  const datasets: any[] = [
    {
      label: accumulationLabel,
      data: accumulationBalances.concat(new Array(ageLabels.length - accumulationBalances.length).fill(null)),
      borderColor: '#10B981',
      backgroundColor: 'rgba(16, 185, 129, 0.08)',
      borderWidth: 2.5,
      tension: 0.4,
      fill: true,
      pointRadius: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === peakAge ? 5 : 0;
      },
      pointBackgroundColor: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === peakAge ? '#10B981' : 'transparent';
      },
      pointBorderColor: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === peakAge ? '#FFFFFF' : 'transparent';
      },
      pointBorderWidth: 2,
      segment: {
        borderColor: (ctx: any) => {
          const age = ageLabels[ctx.p0DataIndex];
          return age >= retirementAge ? 'transparent' : '#10B981';
        }
      }
    },
    {
      label: actuarialLabel,
      data: new Array(retirementIndex).fill(null).concat(retirementBalances),
      borderColor: '#F59E0B',
      backgroundColor: 'rgba(245, 158, 11, 0.08)',
      borderWidth: 2.5,
      tension: 0.4,
      fill: alternativeProjection ? false : true,
      pointRadius: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === exhaustionAge ? 5 : 0;
      },
      pointBackgroundColor: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === exhaustionAge ? '#DC2626' : 'transparent';
      },
      pointBorderColor: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === exhaustionAge ? '#FFFFFF' : 'transparent';
      },
      pointBorderWidth: 2,
      segment: {
        borderColor: (ctx: any) => {
          const age = ageLabels[ctx.p0DataIndex];
          return age < retirementAge ? 'transparent' : '#F59E0B';
        }
      }
    }
  ];

  // Adicionar dataset de comparação se disponível
  if (alternativeProjection) {
    datasets.push({
      label: desiredLabel,
      data: alternativeProjection.balances,
      borderColor: '#EF4444',
      backgroundColor: 'transparent',
      tension: 0.4,
      fill: false,
      borderWidth: 2,
      borderDash: [8, 4],
      pointRadius: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === alternativeProjection?.exhaustionAge ? 5 : 0;
      },
      pointBackgroundColor: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === alternativeProjection?.exhaustionAge ? '#DC2626' : 'transparent';
      },
      pointBorderColor: (context: any) => {
        const age = ageLabels[context.dataIndex];
        return age === alternativeProjection?.exhaustionAge ? '#FFFFFF' : 'transparent';
      },
      pointBorderWidth: 2,
      segment: {
        borderColor: (ctx: any) => {
          const age = ageLabels[ctx.p0DataIndex];
          return age < retirementAge ? 'transparent' : '#EF4444';
        }
      }
    });
  }

  // Adicionar linha de aposentadoria
  datasets.push({
    label: 'Linha de Aposentadoria',
    data: ageLabels.map(age => age === retirementAge ? peakBalance * 1.1 : null),
    borderColor: '#9CA3AF',
    borderWidth: 1.5,
    borderDash: [6, 6],
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
          },
          generateLabels: (chart: any) => {
            const datasets = chart.data.datasets;
            const labels = [];

            // Adicionar contexto integrado no topo da legenda
            const conversionMode = state.cd_conversion_mode || 'ACTUARIAL';
            const modeInfo = getConversionModeInfo(conversionMode);
            const actuarialIncome = results.monthly_income_cd || 0;
            const desiredIncome = state.target_benefit || 0;
            const showComparison = desiredIncome > 0 && Math.abs(desiredIncome - actuarialIncome) > 100;

            // Criar item de contexto integrado
            labels.push({
              text: `${modeInfo.icon} ${modeInfo.label} • Atual: ${formatCurrencyBR(actuarialIncome, 0)}${showComparison ? ` • Meta: ${formatCurrencyBR(desiredIncome, 0)}` : ''}`,
              fillStyle: 'transparent',
              strokeStyle: 'transparent',
              lineWidth: 0,
              pointStyle: 'line',
              hidden: false,
              index: -1,
              fontColor: '#4B5563',
              fontSize: 13,
              fontStyle: 'bold'
            });

            // Adicionar datasets com cores corretas (exceto linha de aposentadoria)
            datasets.forEach((dataset: any, index: number) => {
              if (dataset.label !== 'Linha de Aposentadoria') {
                labels.push({
                  text: dataset.label,
                  fillStyle: dataset.backgroundColor || dataset.borderColor,
                  strokeStyle: dataset.borderColor,
                  lineWidth: dataset.borderWidth || 2,
                  pointStyle: dataset.pointStyle || 'line',
                  hidden: false,
                  index: index,
                  fontColor: '#374151',
                  fontSize: 12
                });
              }
            });

            return labels;
          }
        },
      },
      tooltip: {
        callbacks: {
          title: function(context: any) {
            const age = context[0].label;
            const retirementAge = state.retirement_age || 65;
            const phase = age < retirementAge ? 'Acumulação' : 'Aposentadoria';
            return `Idade: ${age} anos (${phase})`;
          },
          label: function(context: any) {
            const value = context.parsed.y;
            if (value === null || value === undefined) return null;
            return `${context.dataset.label}: ${formatCurrencyBR(value, 0)}`;
          },
          afterLabel: function(context: any) {
            const age = parseInt(context.label);
            const retirementAge = state.retirement_age || 65;
            const conversionMode = state.cd_conversion_mode;

            const labels = [];

            if (age === retirementAge) {
              labels.push('🎯 Idade de aposentadoria');

              // Informação específica da modalidade
              if (conversionMode?.includes('CERTAIN')) {
                const years = conversionMode.split('_')[1].replace('Y', '');
                labels.push(`📅 Início dos ${years} anos de pagamento`);
              } else if (conversionMode === 'ACTUARIAL') {
                labels.push('♾️ Início da renda vitalícia');
              }
            }

            if (age === peakAge && age === retirementAge) {
              labels.push('📈 Pico do saldo acumulado');
            }

            if (age === exhaustionAge) {
              if (conversionMode?.includes('CERTAIN')) {
                labels.push('✅ Fim do prazo de pagamento');
              } else {
                labels.push('⚠️ Exaustão estimada do saldo');
              }
            }

            if (alternativeProjection && age === alternativeProjection?.exhaustionAge) {
              labels.push('🔴 Exaustão no cenário para meta desejada');
            }

            return labels.join('\n');
          },
          footer: function(context: any) {
            const age = parseInt(context[0].label);
            const retirementAge = state.retirement_age || 65;

            if (age < retirementAge) {
              const yearsToRetire = retirementAge - age;
              return `${yearsToRetire} anos para aposentadoria`;
            } else {
              const yearsInRetirement = age - retirementAge;
              return `${yearsInRetirement} anos de aposentadoria`;
            }
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
          text: 'Idade (anos)',
          font: {
            size: 12,
            weight: '500' as const,
          },
          color: '#4B5563',
          padding: { top: 15, bottom: 0 }
        },
        grid: {
          display: false,
        },
        border: {
          display: false, // Remove a linha do eixo
        },
        ticks: {
          display: true,
          maxTicksLimit: 8, // Limita o número de ticks no eixo X
          font: {
            size: 10,
            weight: '400' as const,
          },
          color: '#9CA3AF',
          padding: 6,
        },
      },
      y: {
        title: {
          display: true,
          text: 'Saldo da Conta Individual (R$)',
          font: {
            size: 12,
            weight: '500' as const,
          },
          color: '#4B5563',
          padding: { top: 0, bottom: 15 }
        },
        grid: getCleanGridConfig(),
        border: {
          display: false, // Remove a linha do eixo
        },
        ticks: {
          display: true,
          maxTicksLimit: 5, // Máximo de 5 ticks para visual clean
          font: {
            size: 10,
            weight: '400' as const,
          },
          color: '#9CA3AF',
          padding: 8,
          callback: function(value: any) {
            return formatCompactCurrencyBR(value);
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

      {/* Gráfico com contexto integrado na legenda */}
      <div className="h-[28rem]">
        <Line data={data} options={options} />
      </div>
    </div>
  );
};

export default CDLifecycleChart;