import React from 'react';
import type { SimulatorState } from '../../types';
import { useFormHandler } from '../../hooks';
import { formatCurrencyBR } from '../../utils/formatBR';
import { FormField, CurrencyInput } from '../../design-system/components';

interface ParticipantSectionProps {
  state: SimulatorState;
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const ParticipantSection: React.FC<ParticipantSectionProps> = ({ 
  state, 
  onStateChange, 
  loading 
}) => {
  const { handleInputChange } = useFormHandler({ onStateChange });

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 space-y-4">

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {/* Idade - Refatorado com FormField */}
        <FormField
          label="Idade Atual"
          helper="Idade atual do participante (entre 18 e 75 anos)"
          variant="expanded"
          htmlFor="age"
        >
          <input
            id="age"
            type="number"
            min="18"
            max="75"
            value={state.age}
            onChange={(e) => handleInputChange('age', parseInt(e.target.value))}
            className="w-full px-4 py-4 text-base border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white hover:border-slate-300 shadow-sm"
            disabled={loading}
          />
        </FormField>

        {/* Gênero - Refatorado com FormField */}
        <FormField
          label="Sexo"
          helper="Influencia na seleção da tábua de mortalidade apropriada"
          variant="expanded"
          htmlFor="gender"
        >
          <select
            id="gender"
            value={state.gender}
            onChange={(e) => handleInputChange('gender', e.target.value as 'M' | 'F')}
            className="w-full px-4 py-4 text-base border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white hover:border-slate-300 shadow-sm"
            disabled={loading}
          >
            <option value="M">Masculino</option>
            <option value="F">Feminino</option>
          </select>
        </FormField>

        {/* Salário - Refatorado com FormField */}
        <FormField
          label="Salário Atual"
          helper="Salário mensal bruto atual (base para cálculos)"
          variant="expanded"
          htmlFor="salary"
        >
          <CurrencyInput
            id="salary"
            value={state.salary}
            onValueChange={(value) => handleInputChange('salary', value || 0)}
            disabled={loading}
            allowNegative={false}
            decimalScale={0}
            size="lg"
            variant="default"
          />
        </FormField>

        {/* Tempo de Serviço - Refatorado com FormField */}
        <FormField
          label="Tempo de Serviço"
          helper="Tempo de serviço já acumulado na empresa ou instituição"
          variant="expanded"
          htmlFor="service_years"
        >
          <div className="flex items-center border-2 border-slate-200 rounded-xl bg-white hover:border-slate-300 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all shadow-sm">
            <input
              id="service_years"
              type="number"
              min="0"
              step="0.1"
              value={state.service_years}
              onChange={(e) => handleInputChange('service_years', parseFloat(e.target.value))}
              className="flex-1 px-3 py-3 text-sm bg-transparent border-none focus:outline-none"
              disabled={loading}
            />
            <span className="pr-4 text-slate-500 text-base select-none">anos</span>
          </div>
        </FormField>

        {/* Idade de Aposentadoria - Refatorado com FormField */}
        <FormField
          label="Idade de Aposentadoria"
          helper="Idade planejada para início do recebimento do benefício"
          variant="expanded"
          htmlFor="retirement_age"
        >
          <input
            id="retirement_age"
            type="number"
            min={state.age + 1}
            max="75"
            value={state.retirement_age}
            onChange={(e) => handleInputChange('retirement_age', parseInt(e.target.value))}
            className="w-full px-4 py-4 text-base border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white hover:border-slate-300 shadow-sm"
            disabled={loading}
          />
        </FormField>

        {/* Saldo Inicial - Refatorado com FormField */}
        <FormField
          label="Saldo Inicial"
          helper="Montante já acumulado na conta de aposentadoria individual"
          variant="expanded"
          htmlFor="initial_balance"
        >
          <CurrencyInput
            id="initial_balance"
            value={state.initial_balance}
            onValueChange={(value) => handleInputChange('initial_balance', value || 0)}
            disabled={loading}
            allowNegative={false}
            decimalScale={0}
            placeholder="0"
            size="lg"
            variant="default"
          />
        </FormField>
      </div>

      {/* Resumo Visual */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100">
        <h3 className="text-sm font-bold text-slate-700 mb-3 flex items-center">
          <span className="mr-2">📊</span>
          Resumo do Perfil
        </h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="flex justify-between">
            <span className="text-slate-600 font-medium">Idade atual:</span>
            <span className="font-bold text-slate-800">{state.age} anos</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-600 font-medium">Tempo até aposentar:</span>
            <span className="font-bold text-slate-800">{state.retirement_age - state.age} anos</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-600 font-medium">Salário mensal:</span>
            <span className="font-bold text-slate-800">{formatCurrencyBR(state.salary, 0)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-600 font-medium">Saldo já acumulado:</span>
            <span className="font-bold text-slate-800">{formatCurrencyBR(state.initial_balance, 0)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ParticipantSection;