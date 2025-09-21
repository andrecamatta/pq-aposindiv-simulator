import React from 'react';
import type { SimulatorState } from '../../types';
import { Input, Select, CurrencyInput, RangeSlider } from '../../design-system/components';
import { formatCurrencyBR, formatSimplePercentageBR } from '../../utils/formatBR';
import { useFormHandler, useLifeExpectancy } from '../../hooks';

interface ParticipantTabProps {
  state: SimulatorState;
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const ParticipantTab: React.FC<ParticipantTabProps> = ({ 
  state, 
  onStateChange, 
  loading 
}) => {
  const { handleInputChange } = useFormHandler({ onStateChange });

  // Hook para buscar expectativa de vida
  const lifeExpectancyData = useLifeExpectancy({
    age: state.age || 30,
    gender: state.gender || 'M',
    mortalityTable: state.mortality_table || 'BR_EMS_2021',
    aggravation: state.mortality_aggravation || 0
  });

  const formatLifeExpectancy = (years: number): string => {
    const wholeYears = Math.floor(years);
    const months = Math.round((years - wholeYears) * 12);
    
    if (months === 0) {
      return `${wholeYears} anos`;
    }
    return `${wholeYears} anos e ${months} ${months === 1 ? 'mês' : 'meses'}`;
  };

  const genderOptions = [
    { value: 'M', label: 'Masculino' },
    { value: 'F', label: 'Feminino' }
  ];

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Participante
        </h1>
        <p className="text-gray-600">
          Configure as informações pessoais e financeiras do participante.
        </p>
      </div>

      <div className="bg-white p-8 rounded-lg shadow-md">
        <div className="space-y-8">
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Informações Pessoais</h3>
          <div>
            <Select
              label="Gênero"
              value={state.gender}
              onChange={(value) => handleInputChange('gender', value)}
              options={genderOptions}
              disabled={loading}
            />
            <RangeSlider
              label="Idade Atual"
              value={state.age || 30}
              min={18}
              max={100}
              step={1}
              onChange={(value) => handleInputChange('age', value)}
              suffix=" anos"
              disabled={loading}
            />
            
            {/* Exibição compacta da Expectativa de Vida */}
            <div className="mt-2 text-sm text-gray-600">
              {lifeExpectancyData.loading ? (
                <span className="flex items-center space-x-1">
                  <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                  <span>Calculando expectativa...</span>
                </span>
              ) : lifeExpectancyData.data ? (
                <span>
                  Expectativa de vida: <strong>{formatLifeExpectancy(lifeExpectancyData.data.life_expectancy)}</strong> (até {lifeExpectancyData.data.expected_death_age.toFixed(0)} anos)
                </span>
              ) : lifeExpectancyData.error ? (
                <span className="text-red-500">
                  Expectativa de vida: erro no cálculo
                </span>
              ) : null}
            </div>
          </div>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Informações Financeiras</h3>
          <div>
            <RangeSlider
              label="Salário Mensal"
              value={state.salary || 8000}
              min={1000}
              max={60000}
              step={100}
              onChange={(value) => handleInputChange('salary', value)}
              formatDisplay={formatCurrencyBR}
              disabled={loading}
            />
            <RangeSlider
              label="Saldo Inicial"
              value={state.initial_balance || 0}
              min={0}
              max={1000000}
              step={100}
              onChange={(value) => handleInputChange('initial_balance', value)}
              formatDisplay={formatCurrencyBR}
              disabled={loading}
            />
            <RangeSlider
              label="Crescimento Salarial Real"
              value={state.salary_growth_real || 0.02}
              min={0}
              max={0.05}
              step={0.001}
              onChange={(value) => handleInputChange('salary_growth_real', value)}
              formatDisplay={(v) => formatSimplePercentageBR(v * 100, 2)}
              disabled={loading}
            />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ParticipantTab;
