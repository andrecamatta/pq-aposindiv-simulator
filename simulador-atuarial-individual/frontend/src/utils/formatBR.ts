/**
 * Utilitários de formatação numérica brasileira
 * 
 * Padrão brasileiro:
 * - Decimais: vírgula (,)
 * - Milhares: ponto (.)
 * - Moeda: R$ 1.234,56
 * - Percentual: 12,5%
 */

/**
 * Formata um valor como moeda brasileira (R$)
 * @param value - Valor numérico a ser formatado
 * @param decimals - Número de casas decimais (padrão: 2)
 * @returns String formatada como moeda (ex: "R$ 1.234,56")
 */
export const formatCurrencyBR = (value: number, decimals: number = 2): string => {
  if (isNaN(value) || value === null || value === undefined) {
    return `R$ 0,${'0'.repeat(Math.max(decimals, 2))}`;
  }
  
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
};

/**
 * Formata um número com separadores brasileiros
 * @param value - Valor numérico a ser formatado
 * @param decimals - Número de casas decimais (padrão: 0)
 * @returns String formatada (ex: "1.234,56")
 */
export const formatNumberBR = (value: number, decimals: number = 0): string => {
  if (isNaN(value) || value === null || value === undefined) {
    return decimals > 0 ? `0,${'0'.repeat(decimals)}` : '0';
  }
  
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
};

/**
 * Formata um valor como percentual brasileiro
 * @param value - Valor numérico (ex: 0.15 para 15%)
 * @param decimals - Número de casas decimais (padrão: 1)
 * @param includeSign - Se deve incluir o símbolo % (padrão: true)
 * @returns String formatada (ex: "15,5%")
 */
export const formatPercentageBR = (value: number, decimals: number = 1, includeSign: boolean = true): string => {
  if (isNaN(value) || value === null || value === undefined) {
    return includeSign ? `0,${'0'.repeat(Math.max(decimals, 1))}%` : '0';
  }
  
  const formatted = formatNumberBR(value, decimals);
  return includeSign ? `${formatted}%` : formatted;
};

/**
 * Formata um valor compacto brasileiro (ex: 1,5M, 2,3K)
 * @param value - Valor numérico a ser formatado
 * @returns String formatada de forma compacta (ex: "1,5 mi")
 */
export const formatCompactBR = (value: number): string => {
  if (isNaN(value) || value === null || value === undefined) {
    return '0';
  }

  return new Intl.NumberFormat('pt-BR', {
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(value);
};

/**
 * Formata valores monetários de forma compacta para gráficos
 * @param value - Valor numérico a ser formatado
 * @returns String formatada como moeda compacta (ex: "R$ 1,5M", "R$ 250K")
 */
export const formatCompactCurrencyBR = (value: number): string => {
  if (isNaN(value) || value === null || value === undefined) {
    return 'R$ 0';
  }

  const absValue = Math.abs(value);
  const sign = value < 0 ? '-' : '';

  if (absValue >= 1000000000) {
    return `${sign}R$ ${formatNumberBR(absValue / 1000000000, 1)}B`;
  } else if (absValue >= 1000000) {
    return `${sign}R$ ${formatNumberBR(absValue / 1000000, 1)}M`;
  } else if (absValue >= 1000) {
    return `${sign}R$ ${formatNumberBR(absValue / 1000, 0)}K`;
  } else if (absValue >= 1) {
    return `${sign}R$ ${formatNumberBR(absValue, 0)}`;
  } else {
    return 'R$ 0';
  }
};

/**
 * Formata valor para exibição em sliders (formato compacto brasileiro)
 * @param value - Valor numérico
 * @param unit - Unidade opcional ('k' para milhares, 'M' para milhões)
 * @returns String formatada para slider
 */
export const formatSliderDisplayBR = (value: number, unit?: 'k' | 'M'): string => {
  if (isNaN(value) || value === null || value === undefined) {
    return '0';
  }
  
  if (unit === 'k') {
    return `${formatNumberBR(value / 1000, 1)}k`;
  } else if (unit === 'M') {
    return `${formatNumberBR(value / 1000000, 1)}M`;
  }
  
  return formatNumberBR(value);
};

/**
 * Formata anos para exibição brasileira
 * @param years - Número de anos
 * @returns String formatada (ex: "1 ano", "10 anos")
 */
export const formatYearsBR = (years: number): string => {
  const roundedYears = Math.round(years);
  if (roundedYears === 1) return '1 ano';
  return `${formatNumberBR(roundedYears)} anos`;
};

/**
 * Formata idade para exibição brasileira
 * @param age - Idade em anos
 * @returns String formatada (ex: "65 anos")
 */
export const formatAgeBR = (age: number): string => {
  return `${formatNumberBR(Math.round(age))} anos`;
};

/**
 * Formata percentual simples (para valores já em formato percentual)
 * @param value - Valor já em percentual (ex: 15.5 para 15.5%)
 * @param decimals - Casas decimais (padrão: 1)
 * @returns String formatada (ex: "15,5%")
 */
export const formatSimplePercentageBR = (value: number, decimals: number = 1): string => {
  return formatPercentageBR(value, decimals);
};

/**
 * Formata valor convertendo de decimal para percentual
 * @param value - Valor decimal (ex: 0.155 para 15,5%)
 * @param decimals - Casas decimais (padrão: 1)
 * @returns String formatada (ex: "15,5%")
 */
export const formatDecimalToPercentageBR = (value: number, decimals: number = 1): string => {
  return formatPercentageBR(value * 100, decimals);
};

/**
 * Traduz valores de indexação para português
 * @param indexation - Valor da indexação em inglês
 * @returns String traduzida para português
 */
export const formatIndexationBR = (indexation: string): string => {
  const indexationMap: { [key: string]: string } = {
    'none': 'Nenhuma',
    'salary': 'Salário',
    'custom': 'Customizada'
  };
  
  return indexationMap[indexation] || indexation;
};

/**
 * Traduz modalidades de benefício/conversão para português
 * @param mode - Modalidade em inglês
 * @param planType - Tipo de plano (BD ou CD)
 * @returns String traduzida para português
 */
export const formatBenefitModalityBR = (mode: string, planType: string): string => {
  if (planType === 'CD') {
    const cdModalityMap: { [key: string]: string } = {
      'ACTUARIAL': 'Atuarial',
      'ACTUARIAL_EQUIVALENT': 'Equivalência Atuarial',
      'CERTAIN_5Y': 'Certa 5 anos',
      'CERTAIN_10Y': 'Certa 10 anos',
      'CERTAIN_15Y': 'Certa 15 anos',
      'CERTAIN_20Y': 'Certa 20 anos',
      'PERCENTAGE': 'Percentual',
      'PROGRAMMED': 'Programada'
    };
    return cdModalityMap[mode] || mode;
  } else {
    const bdModalityMap: { [key: string]: string } = {
      'VALUE': 'Valor Fixo',
      'REPLACEMENT_RATE': 'Taxa de Reposição'
    };
    return bdModalityMap[mode] || mode;
  }
};

/**
 * Formata duração em anos com decimais brasileiros
 * @param duration - Duração em anos
 * @param decimals - Casas decimais (padrão: 1)
 * @returns String formatada (ex: "10,5 anos")
 */
export const formatDurationBR = (duration: number, decimals: number = 1): string => {
  const formatted = formatNumberBR(duration, decimals);
  return duration === 1 ? `${formatted} ano` : `${formatted} anos`;
};

/**
 * Formata uma data para o padrão brasileiro
 * @param date - Objeto Date a ser formatado
 * @returns String formatada (ex: "15/03/2024")
 */
export const formatDateBR = (date: Date): string => {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  }).format(date);
};

// Re-exportar com nomes mais curtos para compatibilidade
export const formatCurrency = formatCurrencyBR;
export const formatNumber = formatNumberBR;
export const formatPercentage = formatPercentageBR;
export const formatCompact = formatCompactBR;
export const formatYears = formatYearsBR;
export const formatAge = formatAgeBR;