export const parseNumericValue = (value: string | number, fallback = 0): number => {
  if (typeof value === 'number') return isNaN(value) ? fallback : value;
  
  const parsed = parseFloat(value);
  return isNaN(parsed) ? fallback : parsed;
};

export const parseIntegerValue = (value: string | number, fallback = 0): number => {
  if (typeof value === 'number') return isNaN(value) ? fallback : Math.round(value);
  
  const parsed = parseInt(value);
  return isNaN(parsed) ? fallback : parsed;
};

export const parsePercentageValue = (value: string | number, fallback = 0): number => {
  const numericValue = parseNumericValue(value, fallback);
  return numericValue / 100;
};

export const createInputParser = (type: 'float' | 'int' | 'percentage') => {
  return (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    
    switch (type) {
      case 'int':
        return parseIntegerValue(value);
      case 'percentage':
        return parsePercentageValue(value);
      case 'float':
      default:
        return parseNumericValue(value);
    }
  };
};

export const validateAge = (age: number): boolean => {
  return age >= 18 && age <= 100;
};

export const validateSalary = (salary: number): boolean => {
  return salary > 0 && salary <= 1000000;
};

export const validatePercentage = (value: number, min = 0, max = 1): boolean => {
  return value >= min && value <= max;
};

export const createValidationConfig = () => ({
  age: {
    min: 18,
    max: 100,
    validator: validateAge,
    parser: parseIntegerValue,
    errorMessage: 'Idade deve estar entre 18 e 100 anos'
  },
  salary: {
    min: 0,
    max: 1000000,
    validator: validateSalary,
    parser: parseNumericValue,
    errorMessage: 'Salário deve ser maior que zero'
  },
  percentage: {
    min: 0,
    max: 100,
    validator: (value: number) => validatePercentage(value / 100),
    parser: parseNumericValue,
    errorMessage: 'Valor deve estar entre 0% e 100%'
  }
});