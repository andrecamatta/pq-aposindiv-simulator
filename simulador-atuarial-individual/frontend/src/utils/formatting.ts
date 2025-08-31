/**
 * Utilitários de formatação para valores monetários, percentuais e números
 */

/**
 * Formata um valor como moeda brasileira (R$)
 * @param value - Valor numérico a ser formatado
 * @param decimals - Número de casas decimais (padrão: 2)
 * @returns String formatada como moeda
 */
export const formatCurrency = (value: number, decimals: number = 2): string => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
};

/**
 * Formata um valor como percentual
 * @param value - Valor numérico a ser formatado (ex: 0.15 para 15%)
 * @param decimals - Número de casas decimais (padrão: 1)
 * @param includeSign - Se deve incluir o símbolo % (padrão: true)
 * @returns String formatada como percentual
 */
export const formatPercentage = (value: number, decimals: number = 1, includeSign: boolean = true): string => {
  const formatted = value.toFixed(decimals);
  return includeSign ? `${formatted}%` : formatted;
};

/**
 * Formata um número com separadores de milhares
 * @param value - Valor numérico a ser formatado
 * @param decimals - Número de casas decimais (padrão: 0)
 * @returns String formatada com separadores
 */
export const formatNumber = (value: number, decimals: number = 0): string => {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
};

/**
 * Formata um valor compacto (ex: 1.5M, 2.3K)
 * @param value - Valor numérico a ser formatado
 * @returns String formatada de forma compacta
 */
export const formatCompact = (value: number): string => {
  return new Intl.NumberFormat('pt-BR', {
    notation: 'compact',
    maximumFractionDigits: 1
  }).format(value);
};

/**
 * Formata anos para exibição (ex: "10 anos")
 * @param years - Número de anos
 * @returns String formatada
 */
export const formatYears = (years: number): string => {
  if (years === 1) return '1 ano';
  return `${years} anos`;
};

/**
 * Formata idade para exibição
 * @param age - Idade em anos
 * @returns String formatada
 */
export const formatAge = (age: number): string => {
  return `${age} anos`;
};