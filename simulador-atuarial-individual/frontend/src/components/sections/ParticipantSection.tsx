import React from 'react';
import type { SimulatorState } from '../../types';
import { useFormHandler } from '../../hooks';
import { formatCurrencyBR } from '../../utils/formatBR';

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
        {/* Idade */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
            Idade Atual
          </label>
          <input
            type="number"
            min="18"
            max="75"
            value={state.age}
            onChange={(e) => handleInputChange('age', parseInt(e.target.value))}
            className="w-full px-4 py-4 text-base border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white hover:border-slate-300 shadow-sm"
            disabled={loading}
          />
          <p className="text-xs text-slate-500 leading-tight mt-1">
            Idade atual do participante (entre 18 e 75 anos)
          </p>
        </div>

        {/* Gênero */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
            Sexo
          </label>
          <select
            value={state.gender}
            onChange={(e) => handleInputChange('gender', e.target.value as 'M' | 'F')}
            className="w-full px-4 py-4 text-base border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white hover:border-slate-300 shadow-sm"
            disabled={loading}
          >
            <option value="M">Masculino</option>
            <option value="F">Feminino</option>
          </select>
          <p className="text-xs text-slate-500 leading-tight mt-1">
            Influencia na seleção da tábua de mortalidade apropriada
          </p>
        </div>

        {/* Salário */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
            Salário Atual
          </label>
          <div className="flex items-center border border-slate-200 rounded-lg bg-white hover:border-slate-300 focus-within:ring-1 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all">
            <span className="pl-3 text-slate-500 text-xs select-none font-medium">R$</span>
            <input
              type="number"
              min="0"
              step="100"
              value={state.salary}
              onChange={(e) => handleInputChange('salary', parseFloat(e.target.value))}
              className="flex-1 px-2 py-2 text-sm bg-transparent border-none focus:outline-none"
              disabled={loading}
              placeholder="0"
            />
          </div>
          <p className="text-xs text-slate-500 leading-tight mt-1">
            Salário mensal bruto atual (base para cálculos)
          </p>
        </div>

        {/* Tempo de Serviço */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
            Tempo de Serviço
          </label>
          <div className="flex items-center border-2 border-slate-200 rounded-xl bg-white hover:border-slate-300 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all shadow-sm">
            <input
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
          <p className="text-xs text-slate-500 leading-tight mt-1">
            Tempo de serviço já acumulado na empresa ou instituição
          </p>
        </div>

        {/* Idade de Aposentadoria */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
            Idade de Aposentadoria
          </label>
          <input
            type="number"
            min={state.age + 1}
            max="75"
            value={state.retirement_age}
            onChange={(e) => handleInputChange('retirement_age', parseInt(e.target.value))}
            className="w-full px-4 py-4 text-base border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white hover:border-slate-300 shadow-sm"
            disabled={loading}
          />
          <p className="text-xs text-slate-500 leading-tight mt-1">
            Idade planejada para início do recebimento do benefício
          </p>
        </div>

        {/* Saldo Inicial */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wide mb-1">
            Saldo Inicial
          </label>
          <div className="flex items-center border border-slate-200 rounded-lg bg-white hover:border-slate-300 focus-within:ring-1 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all">
            <span className="pl-3 text-slate-500 text-xs select-none font-medium">R$</span>
            <input
              type="number"
              min="0"
              step="1000"
              value={state.initial_balance}
              onChange={(e) => handleInputChange('initial_balance', parseFloat(e.target.value))}
              className="flex-1 px-2 py-2 text-sm bg-transparent border-none focus:outline-none"
              disabled={loading}
              placeholder="0"
            />
          </div>
          <p className="text-xs text-slate-500 leading-tight mt-1">
            Montante já acumulado na conta de aposentadoria individual
          </p>
        </div>
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