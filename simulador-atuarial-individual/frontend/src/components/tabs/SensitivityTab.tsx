import React, { useState, useMemo } from 'react';
import { Icon } from '../../design-system/components/Icon';
import TornadoChart, { type TornadoItem } from '../charts/TornadoChart';
import type { SimulatorResults, SimulatorState } from '../../types/simulator.types';
import { formatCurrencyBR } from '../../utils/formatBR';

interface SensitivityTabProps {
  results: SimulatorResults | null;
  state: SimulatorState;
  loading: boolean;
}

type CDMetric = 'monthly_income' | 'replacement_ratio';

const SensitivityTab: React.FC<SensitivityTabProps> = ({
  results,
  state,
  loading
}) => {
  const [selectedMetric, setSelectedMetric] = useState<CDMetric>('monthly_income');
  

  // Mapeamento de nomes técnicos para nomes amigáveis
  const variableNames: Record<string, string> = {
    'sensitivity_discount_rate': 'Taxa de Desconto (a.a.)',
    'sensitivity_mortality': 'Tábua de Mortalidade',
    'sensitivity_retirement_age': 'Idade de Aposentadoria',
    'sensitivity_salary_growth': 'Crescimento Salarial (a.a.)',
    'sensitivity_inflation': 'Inflação (a.a.)', // Mantido oculto por enquanto
  };

  // Tooltips explicativos para cada variável (atualizado para déficit/superávit)
  const variableTooltips: Record<string, string> = {
    'sensitivity_discount_rate': 'Taxa usada para descontar valores futuros a valor presente. Taxas maiores reduzem as reservas necessárias, melhorando o superávit.',
    'sensitivity_mortality': 'Tábua que determina as probabilidades de morte. Tábuas com maior mortalidade reduzem os benefícios esperados, melhorando o superávit.',
    'sensitivity_retirement_age': 'Idade em que o benefício inicia. Idades maiores reduzem o período de pagamento, melhorando o superávit.',
    'sensitivity_salary_growth': 'Taxa de crescimento real dos salários. Maiores taxas aumentam contribuições e benefícios futuros - impacto líquido no superávit.',
    'sensitivity_inflation': 'Taxa de inflação para reajuste de benefícios. Maiores taxas aumentam o valor presente dos benefícios, piorando o superávit.',
  };

  // Função para extrair extremos de um dicionário de sensibilidade
  const getExtremes = (dict: Record<string | number, number>, variableName?: string) => {
    console.log(`[Sensibilidade] Analisando ${variableName}:`, dict);
    
    if (!dict || typeof dict !== 'object') {
      console.warn(`[Sensibilidade] ${variableName}: dados inválidos`, dict);
      return null;
    }
    
    const entries = Object.entries(dict);
    if (!entries.length) {
      console.warn(`[Sensibilidade] ${variableName}: dicionário vazio`);
      return null;
    }
    
    console.log(`[Sensibilidade] ${variableName}: encontradas ${entries.length} entradas`);
    
    // Separar lógica para números vs strings
    const firstKey = entries[0][0];
    const isNumericKeys = !isNaN(Number(firstKey));
    
    let sorted;
    if (isNumericKeys) {
      // Chaves numéricas: converter para números e ordenar numericamente
      sorted = entries
        .map(([k, v]) => [Number(k), v] as [number, number])
        .sort((a, b) => a[0] - b[0]);
      
      console.log(`[Sensibilidade] ${variableName}: ordenação numérica`, sorted);
    } else {
      // Chaves string (ex: tábuas de mortalidade): usar valor como ordenação
      sorted = entries
        .map(([k, v]) => [k, v] as [string, number])
        .sort((a, b) => a[1] - b[1]); // Ordenar por valor, não por chave
      
      console.log(`[Sensibilidade] ${variableName}: ordenação por valor`, sorted);
    }
    
    const [lowK, lowV] = sorted[0];
    const [highK, highV] = sorted[sorted.length - 1];
    
    // Criar range formatado para labels
    let range = '';
    if (isNumericKeys) {
      // Para valores numéricos, formatar adequadamente
      const lowFormatted = typeof lowK === 'number' && lowK < 1 ? 
        (lowK * 100).toFixed(1) + '%' : 
        lowK.toString();
      const highFormatted = typeof highK === 'number' && highK < 1 ? 
        (highK * 100).toFixed(1) + '%' : 
        highK.toString();
      range = `${lowFormatted} → ${highFormatted}`;
    } else {
      range = `${lowK} → ${highK}`;
    }
    
    const result = { lowK, lowV, highK, highV, range, isNumeric: isNumericKeys };
    console.log(`[Sensibilidade] ${variableName}: extremos`, result);
    
    return result;
  };

  // Dados de fallback para demonstração centrados nos valores atuais do usuário
  const getMockSensitivityData = (baseline: number, userState: SimulatorState) => {
    // Taxa de desconto centrada no valor atual do usuário ±1%
    const currentDiscount = userState.discount_rate;
    const discountLow = Math.max(0.001, currentDiscount - 0.01);
    const discountHigh = currentDiscount + 0.01;
    
    // Idade de aposentadoria centrada no valor atual do usuário ±1 ano
    const currentRetirement = userState.retirement_age;
    const retirementLow = Math.max(userState.age + 1, currentRetirement - 1);
    const retirementHigh = Math.min(75, currentRetirement + 1);
    
    // Crescimento salarial centrado no valor atual do usuário ±1%
    const currentSalaryGrowth = userState.salary_growth_real;
    const salaryGrowthLow = Math.max(0.0, currentSalaryGrowth - 0.01);
    const salaryGrowthHigh = currentSalaryGrowth + 0.01;
    
    return {
      sensitivity_discount_rate: {
        [discountLow]: baseline * 1.15,     // atual-1%: impacto alto (+ reservas)
        [currentDiscount]: baseline * 1.00, // atual: valor base
        [discountHigh]: baseline * 0.85     // atual+1%: impacto baixo (- reservas)
      },
      sensitivity_mortality: {
        'AT_2000_MASC': baseline * 0.95,
        'IBGE_2018_MASC': baseline * 1.00,
        'BR_EMS_2010_MASC': baseline * 1.05
      },
      sensitivity_retirement_age: {
        [retirementLow]: baseline * 1.20,     // atual-1 ano: mais tempo de benefício (+ reservas)
        [currentRetirement]: baseline * 1.00, // atual: valor base
        [retirementHigh]: baseline * 0.85     // atual+1 ano: menos tempo de benefício (- reservas)
      },
      sensitivity_salary_growth: {
        [salaryGrowthLow]: baseline * 0.90,     // atual-1%: menores contribuições (- reservas)
        [currentSalaryGrowth]: baseline * 1.00, // atual: valor base
        [salaryGrowthHigh]: baseline * 1.08     // atual+1%: maiores contribuições (+ reservas)
      }
    };
  };

  // Processar dados de sensibilidade para BD
  const processBDSensitivity = (results: SimulatorResults): TornadoItem[] => {
    console.log('[Sensibilidade] Processando BD - Dados recebidos:', {
      deficit_surplus: results.deficit_surplus,
      deficit_discount_rate: results.sensitivity_deficit_discount_rate,
      deficit_mortality: results.sensitivity_deficit_mortality,
      deficit_retirement_age: results.sensitivity_deficit_retirement_age,
      deficit_salary_growth: results.sensitivity_deficit_salary_growth,
      rmba_fallback: results.rmba
    });

    // NOVA LÓGICA: usar déficit/superávit como baseline (mais útil para análise)
    const baseline = results.deficit_surplus;
    const items: TornadoItem[] = [];

    // Verificar se temos dados de déficit (preferencial) ou usar RMBA (fallback)
    const hasDeficitData = Object.keys(results.sensitivity_deficit_discount_rate || {}).length > 0 ||
                          Object.keys(results.sensitivity_deficit_mortality || {}).length > 0 ||
                          Object.keys(results.sensitivity_deficit_retirement_age || {}).length > 0 ||
                          Object.keys(results.sensitivity_deficit_salary_growth || {}).length > 0;
    
    const hasRmbaData = Object.keys(results.sensitivity_discount_rate || {}).length > 0 ||
                        Object.keys(results.sensitivity_mortality || {}).length > 0 ||
                        Object.keys(results.sensitivity_retirement_age || {}).length > 0 ||
                        Object.keys(results.sensitivity_salary_growth || {}).length > 0;

    let sensitivityData;
    let useDeficitMode = false;
    
    if (hasDeficitData) {
      console.log('[Sensibilidade] BD: usando dados de déficit/superávit (preferencial)');
      useDeficitMode = true;
      sensitivityData = {
        sensitivity_discount_rate: results.sensitivity_deficit_discount_rate,
        sensitivity_mortality: results.sensitivity_deficit_mortality,
        sensitivity_retirement_age: results.sensitivity_deficit_retirement_age,
        sensitivity_salary_growth: results.sensitivity_deficit_salary_growth
      };
    } else if (hasRmbaData) {
      console.log('[Sensibilidade] BD: usando dados RMBA (fallback)');
      useDeficitMode = false;
      sensitivityData = {
        sensitivity_discount_rate: results.sensitivity_discount_rate,
        sensitivity_mortality: results.sensitivity_mortality,
        sensitivity_retirement_age: results.sensitivity_retirement_age,
        sensitivity_salary_growth: results.sensitivity_salary_growth
      };
    } else {
      console.log('[Sensibilidade] BD: usando dados de demonstração (backend vazio)');
      useDeficitMode = false;
      sensitivityData = getMockSensitivityData(baseline, state);
    }

    // Taxa de Desconto
    const discountRate = getExtremes(sensitivityData.sensitivity_discount_rate, 'Taxa de Desconto');
    if (discountRate) {
      items.push({
        label: `${variableNames.sensitivity_discount_rate} (${discountRate.range})`,
        deltaLow: discountRate.lowV - baseline,
        deltaHigh: discountRate.highV - baseline,
        unit: 'R$',
        tooltip: variableTooltips.sensitivity_discount_rate
      });
    }

    // Tábua de Mortalidade
    const mortality = getExtremes(sensitivityData.sensitivity_mortality, 'Mortalidade');
    if (mortality) {
      items.push({
        label: `${variableNames.sensitivity_mortality} (${mortality.range})`,
        deltaLow: mortality.lowV - baseline,
        deltaHigh: mortality.highV - baseline,
        unit: 'R$',
        tooltip: variableTooltips.sensitivity_mortality
      });
    }

    // Idade de Aposentadoria
    const retirementAge = getExtremes(sensitivityData.sensitivity_retirement_age, 'Idade Aposentadoria');
    if (retirementAge) {
      items.push({
        label: `${variableNames.sensitivity_retirement_age} (${retirementAge.range})`,
        deltaLow: retirementAge.lowV - baseline,
        deltaHigh: retirementAge.highV - baseline,
        unit: 'R$',
        tooltip: variableTooltips.sensitivity_retirement_age
      });
    }

    // Crescimento Salarial
    const salaryGrowth = getExtremes(sensitivityData.sensitivity_salary_growth, 'Crescimento Salarial');
    if (salaryGrowth) {
      items.push({
        label: `${variableNames.sensitivity_salary_growth} (${salaryGrowth.range})`,
        deltaLow: salaryGrowth.lowV - baseline,
        deltaHigh: salaryGrowth.highV - baseline,
        unit: 'R$',
        tooltip: variableTooltips.sensitivity_salary_growth
      });
    }

    // Inflação (omitida se vazia)
    if (Object.keys(results.sensitivity_inflation).length > 0) {
      const inflation = getExtremes(results.sensitivity_inflation, 'Inflação');
      if (inflation) {
        items.push({
          label: `${variableNames.sensitivity_inflation} (${inflation.range})`,
          deltaLow: inflation.lowV - baseline,
          deltaHigh: inflation.highV - baseline,
          unit: 'R$',
          tooltip: variableTooltips.sensitivity_inflation
        });
      }
    }

    console.log(`[Sensibilidade] BD: gerados ${items.length} itens para o tornado`);
    return items;
  };

  // Processar dados de sensibilidade para CD
  const processCDSensitivity = (results: SimulatorResults, metric: CDMetric): TornadoItem[] => {
    console.log('[Sensibilidade] Processando CD - Dados recebidos:', {
      monthly_income_cd: results.monthly_income_cd,
      replacement_ratio: results.replacement_ratio,
      metric: metric,
      sensitivity_data: {
        discount_rate: results.sensitivity_discount_rate,
        mortality: results.sensitivity_mortality,
        retirement_age: results.sensitivity_retirement_age,
        salary_growth: results.sensitivity_salary_growth
      }
    });

    // Usar baseline correto baseado na métrica
    const baseline = metric === 'monthly_income' 
      ? (results.monthly_income_cd || 0)
      : (results.replacement_ratio || 0);
    
    const unit = metric === 'monthly_income' ? 'R$' : '%'; // Unidade dinâmica
    const items: TornadoItem[] = [];

    // Para CD, os dados de sensibilidade estão nos mesmos campos, mas com valores de renda mensal
    if (results.sensitivity_discount_rate && Object.keys(results.sensitivity_discount_rate).length > 0) {
      const discountRate = getExtremes(results.sensitivity_discount_rate, 'Taxa de Acumulação CD');
      if (discountRate) {
        items.push({
          label: `Taxa de Acumulação (${discountRate.range})`,
          deltaLow: discountRate.lowV - baseline,
          deltaHigh: discountRate.highV - baseline,
          unit: unit,
          tooltip: 'Taxa de rentabilidade durante o período de acumulação. Taxas maiores geram saldos maiores.'
        });
      }
    }

    if (results.sensitivity_retirement_age && Object.keys(results.sensitivity_retirement_age).length > 0) {
      const retirementAge = getExtremes(results.sensitivity_retirement_age, 'Idade Aposentadoria CD');
      if (retirementAge) {
        items.push({
          label: `Idade de Aposentadoria (${retirementAge.range})`,
          deltaLow: retirementAge.lowV - baseline,
          deltaHigh: retirementAge.highV - baseline,
          unit: unit,
          tooltip: 'Idade em que inicia a conversão em renda. Mais tempo de acumulação aumenta o saldo.'
        });
      }
    }

    if (results.sensitivity_salary_growth && Object.keys(results.sensitivity_salary_growth).length > 0) {
      const salaryGrowth = getExtremes(results.sensitivity_salary_growth, 'Crescimento Salarial CD');
      if (salaryGrowth) {
        items.push({
          label: `Crescimento Salarial (${salaryGrowth.range})`,
          deltaLow: salaryGrowth.lowV - baseline,
          deltaHigh: salaryGrowth.highV - baseline,
          unit: unit,
          tooltip: 'Taxa de crescimento real dos salários. Maiores taxas aumentam as contribuições futuras.'
        });
      }
    }

    console.log(`[Sensibilidade] CD: gerados ${items.length} itens para o tornado`);
    return items;
  };

  // Calcular itens do tornado baseado no tipo de plano
  const tornadoItems = useMemo(() => {
    if (!results) return [];
    
    const planType = state?.plan_type || 'BD'; // CORREÇÃO: usar mesmo padrão do resto do código
    
    if (planType === 'BD') {
      return processBDSensitivity(results);
    } else {
      return processCDSensitivity(results, selectedMetric);
    }
  }, [results, state?.plan_type, selectedMetric]);

  // Baseline para o gráfico
  const baseline = useMemo(() => {
    if (!results) {
      return 0;
    }
    
    const planType = state?.plan_type || 'BD';
    
    if (planType === 'BD') {
      // NOVA LÓGICA: usar déficit/superávit como baseline (mais útil)
      // Verificar se temos dados de déficit disponíveis
      const hasDeficitData = Object.keys(results.sensitivity_deficit_discount_rate || {}).length > 0;
      
      if (hasDeficitData || results.deficit_surplus != null) {
        console.log('[Baseline] BD: usando déficit/superávit:', results.deficit_surplus);
        return results.deficit_surplus;
      } else {
        console.log('[Baseline] BD: fallback para RMBA:', results.rmba);
        return results.rmba || 0;
      }
    } else {
      // Para CD, usar o campo correto baseado na métrica selecionada
      if (selectedMetric === 'monthly_income') {
        // Se monthly_income_cd não está disponível, calcular baseado em replacement_ratio
        let monthlyIncome = results.monthly_income_cd;
        
        if (!monthlyIncome && results.replacement_ratio && state?.salary) {
          // Calcular renda mensal aproximada: salário atual × taxa de reposição / 100
          const monthlyPayments = state.benefit_months_per_year || 13;
          const monthlySalary = state.salary * (state.salary_months_per_year || 13) / 12;
          monthlyIncome = monthlySalary * (results.replacement_ratio / 100);
        }
        
        return monthlyIncome || 0;
      } else {
        return results.replacement_ratio || 0;
      }
    }
  }, [results, state?.plan_type, state?.salary, state?.benefit_months_per_year, state?.salary_months_per_year, selectedMetric]);


  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="h-6 bg-gray-200 rounded w-1/2"></div>
              <div className="h-96 bg-gray-200 rounded"></div>
            </div>
            <div className="space-y-4">
              <div className="h-6 bg-gray-200 rounded w-1/2"></div>
              <div className="h-40 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Icon name="target" size="xl" className="text-gray-400 mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">Execute a Simulação</h3>
          <p className="text-gray-500">
            Configure os parâmetros nas abas anteriores e execute o cálculo para ver a análise de sensibilidade.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Análise de Sensibilidade</h2>
        </div>

        {/* Seletor de métrica (apenas para CD) */}
        {state.plan_type === 'CD' && (
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700">Métrica:</span>
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setSelectedMetric('monthly_income')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  selectedMetric === 'monthly_income'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Renda Mensal
              </button>
              <button
                onClick={() => setSelectedMetric('replacement_ratio')}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  selectedMetric === 'replacement_ratio'
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Taxa de Reposição
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      {state.plan_type === 'CD' && tornadoItems.length === 0 ? (
        // Placeholder para CD quando dados não estão disponíveis
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-start gap-4">
            <Icon name="info" size="lg" className="text-blue-600 mt-1" />
            <div>
              <h3 className="text-lg font-medium text-blue-900 mb-2">
                Análise de Sensibilidade para CD
              </h3>
              <p className="text-blue-800 mb-4">
                A análise de sensibilidade para planos de Contribuição Definida estará disponível em breve.
                Por enquanto, esta funcionalidade está otimizada para planos de Benefício Definido.
              </p>
              <div className="text-sm text-blue-700">
                <p className="font-medium mb-1">Próximas funcionalidades:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Sensibilidade da taxa de acumulação</li>
                  <li>Impacto da taxa de conversão</li>
                  <li>Variação por idade de aposentadoria</li>
                  <li>Análise de cenários para renda mensal</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      ) : tornadoItems.length > 0 ? (
        <div className="flex justify-center">
          {/* Tornado Principal - Layout Centralizado */}
          <div className="bg-white p-8 rounded-lg border border-gray-200 w-full max-w-4xl">
            {/* Header dinâmico com métrica e baseline */}
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Icon name="bar-chart" size="md" className="text-blue-600" />
                  <h3 className="text-xl font-semibold text-gray-900">
                    {(state.plan_type || 'BD') === 'BD' ? 'Análise de Sensibilidade - Impacto no Superávit/Déficit' : 
                     selectedMetric === 'monthly_income' ? 'Análise de Sensibilidade - Impacto na Renda Mensal' : 'Análise de Sensibilidade - Impacto na Taxa de Reposição'}
                  </h3>
                </div>
                <div className="flex items-center gap-2 text-xs text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
                  <Icon name="target" size="xs" />
                  <span>Variações ±1 unidade</span>
                </div>
              </div>
              
              <div className="text-sm text-gray-600 mb-2">
                <span className="font-medium">Valor Base: </span>
                <span className="text-blue-600 font-semibold text-lg">
                  {(() => {
                    const planType = state?.plan_type || 'BD';
                    const isMoney = planType === 'BD' || (planType === 'CD' && selectedMetric === 'monthly_income');
                    const displayValue = isMoney 
                      ? formatCurrencyBR(baseline)
                      : `${baseline.toFixed(1)}%`;
                    
                    return displayValue;
                  })()}
                </span>
              </div>
              <p className="text-sm text-gray-500">
                Análise do impacto de variações nas principais variáveis atuariais, centradas nos valores atualmente configurados
              </p>
            </div>
            
            <TornadoChart
              items={tornadoItems}
              baseline={baseline}
              title=""
              height={450}
            />
          </div>
        </div>
      ) : (
        // Sem dados de sensibilidade
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Icon name="bar-chart" size="xl" className="text-gray-400 mb-4" />
            <h3 className="text-xl font-medium text-gray-900 mb-2">Dados de Sensibilidade Indisponíveis</h3>
            <p className="text-gray-500">
              Execute a simulação novamente ou verifique se todas as premissas estão configuradas.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SensitivityTab;