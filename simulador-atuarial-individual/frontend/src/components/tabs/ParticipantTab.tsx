import React from 'react';
import type { SimulatorState } from '../../types';
import { Input, Select, CurrencyInput, RangeSlider } from '../../design-system/components';
import { formatCurrencyBR, formatSimplePercentageBR } from '../../utils/formatBR';
import { useFormHandler } from '../../hooks';

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

  const genderOptions = [
    { value: 'M', label: 'Masculino' },
    { value: 'F', label: 'Feminino' }
  ];

  return (
    <div className="lg:col-span-2 bg-white p-8 rounded-lg shadow-md">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Dados do Participante</h2>
        <p className="text-gray-600 mt-1">Configure as informações pessoais e financeiras do participante.</p>
      </div>
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
  );
};

export default ParticipantTab;
