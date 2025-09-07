import React from 'react';
import type { SimulatorState, MortalityTable } from '../../types';
import { RangeSlider } from '../../design-system/components';
import { useFormHandler } from '../../hooks';

interface ParametersSectionProps {
  state: SimulatorState;
  mortalityTables: MortalityTable[];
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const ParametersSection: React.FC<ParametersSectionProps> = ({ 
  state, 
  mortalityTables, 
  onStateChange, 
  loading 
}) => {
  const { handleInputChange } = useFormHandler({ onStateChange });

  return (
    <div className="max-w-5xl space-y-6">
      {/* Objetivo */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
        <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center border-b border-slate-100 pb-2">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
            <span className="text-blue-600 text-lg">🎯</span>
          </div>
          Objetivo do Plano
        </h3>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <RangeSlider
            label="Benefício Desejado"
            value={state.target_benefit}
            min={1000}
            max={20000}
            step={100}
            onChange={(value) => handleInputChange('target_benefit', value)}
            tooltip="Valor mensal desejado de aposentadoria"
            formatDisplay={(v) => `${(v/1000).toFixed(1)}k`}
            suffix=" mil"
            disabled={loading}
          />
          <RangeSlider
            label="Taxa de Contribuição"
            value={state.contribution_rate}
            min={0}
            max={25}
            step={0.5}
            onChange={(value) => handleInputChange('contribution_rate', value)}
            formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
            suffix="%"
            tooltip="Percentual do salário destinado à contribuição mensal"
            disabled={loading}
          />
        </div>
      </div>

      {/* Premissas Financeiras */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
        <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center border-b border-slate-100 pb-2">
          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-4">
            <span className="text-green-600 text-lg">💰</span>
          </div>
          Premissas Financeiras
        </h3>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
          <RangeSlider
            label="Taxa de Acumulação Real"
            value={state.accrual_rate}
            min={0}
            max={12}
            step={0.1}
            onChange={(value) => handleInputChange('accrual_rate', value)}
            formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
            suffix="%"
            tooltip="Rentabilidade real anual esperada dos investimentos (já descontada a inflação)"
            disabled={loading}
          />
          <RangeSlider
            label="Taxa de Desconto Real"
            value={state.discount_rate}
            min={0}
            max={0.15}
            step={0.001}
            onChange={(value) => handleInputChange('discount_rate', value)}
            suffix="%"
            tooltip="Taxa real usada para calcular o valor presente das obrigações"
            formatDisplay={(v) => (v * 100).toFixed(2).replace('.', ',')}
            disabled={loading}
          />
          <RangeSlider
            label="Crescimento Salarial Real"
            value={state.salary_growth_real}
            min={0}
            max={0.10}
            step={0.001}
            onChange={(value) => handleInputChange('salary_growth_real', value)}
            suffix="%"
            tooltip="Crescimento real anual dos salários (em termos reais, já descontada a inflação)"
            formatDisplay={(v) => (v * 100).toFixed(2).replace('.', ',')}
            disabled={loading}
          />
        </div>
      </div>

      {/* Base Atuarial */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow">
        <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center border-b border-slate-100 pb-2">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mr-4">
            <span className="text-purple-600 text-lg">📊</span>
          </div>
          Base Atuarial
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="space-y-4">
            <label className="block text-base font-semibold text-slate-700 mb-2">Tábua de Mortalidade</label>
            <select
              value={state.mortality_table}
              onChange={(e) => handleInputChange('mortality_table', e.target.value)}
              className="w-full px-4 py-4 text-base border-2 border-slate-200 rounded-xl bg-white hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm"
              disabled={loading}
            >
              {mortalityTables.map((table) => (
                <option key={table.code} value={table.code}>
                  {table.code} {table.regulatory_approved && '✓'}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-4">
            <label className="block text-base font-semibold text-slate-700 mb-2">Método de Cálculo Atuarial</label>
            <select
              value={state.calculation_method}
              onChange={(e) => handleInputChange('calculation_method', e.target.value as 'PUC' | 'EAN')}
              className="w-full px-4 py-4 text-base border-2 border-slate-200 rounded-xl bg-white hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-sm"
              disabled={loading}
            >
              <option value="PUC">PUC - Projected Unit Credit</option>
              <option value="EAN">EAN - Entry Age Normal</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ParametersSection;