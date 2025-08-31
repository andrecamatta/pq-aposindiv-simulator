export const formatCurrency = (value: number, decimals = 2): string => {
  if (isNaN(value) || value === null || value === undefined) {
    return `R$ 0,${'0'.repeat(Math.max(decimals, 2))}`;
  }
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

export const formatNumber = (value: number, decimals = 0): string => {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

export const formatPercentage = (value: number, decimals = 2): string => {
  return `${formatNumber(value, decimals)}%`;
};