import React, { useRef, useState, useCallback } from 'react';
import type { SimulatorState, MortalityTable } from '../types';
import { Icon } from '../design-system/components/Icon';
import { useFormHandler } from '../hooks';

interface ParameterPanelProps {
  state: SimulatorState;
  mortalityTables: MortalityTable[];
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const ParameterPanel: React.FC<ParameterPanelProps> = ({
  state,
  mortalityTables,
  onStateChange,
  loading
}) => {
  const { handleInputChange } = useFormHandler({ onStateChange });

  const SliderField = ({ 
    label, 
    field, 
    min, 
    max, 
    step, 
    value, 
    suffix = '', 
    tooltip = '',
    formatDisplay = (v: number) => v.toString()
  }: {
    label: string;
    field: keyof SimulatorState;
    min: number;
    max: number;
    step: number;
    value: number;
    suffix?: string;
    tooltip?: string;
    formatDisplay?: (value: number) => string;
  }) => (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1">
          <label className="text-xs font-medium text-gray-700">{label}</label>
          {tooltip && (
            <div className="relative group">
              <Icon name="info" className="h-3 w-3 text-gray-400 cursor-help" />
              <div className="invisible group-hover:visible absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 text-xs text-white bg-gray-900 rounded shadow-lg whitespace-nowrap z-10">
                {tooltip}
              </div>
            </div>
          )}
        </div>
        <span className="text-xs font-medium text-blue-600">{formatDisplay(value)}{suffix}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => handleInputChange(field, parseFloat(e.target.value))}
        className="w-full slider"
        disabled={loading}
      />
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow-lg p-4 space-y-4 max-w-md">
      <h2 className="text-lg font-bold text-gray-900 border-b pb-2">
        <div className="flex items-center gap-2">
          <Icon name="file-text" size="sm" className="text-gray-700" />
          Parâmetros
        </div>
      </h2>

      {/* Dados do Participante */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
          <Icon name="user" size="sm" className="text-gray-700" />
          Participante
        </h3>
        
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Idade</label>
            <input
              type="number"
              min="18"
              max="70"
              value={state.age}
              onChange={(e) => handleInputChange('age', parseInt(e.target.value))}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={loading}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Sexo</label>
            <select
              value={state.gender}
              onChange={(e) => handleInputChange('gender', e.target.value as 'M' | 'F')}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={loading}
            >
              <option value="M">M</option>
              <option value="F">F</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Salário (R$)</label>
            <input
              type="number"
              min="0"
              step="100"
              value={state.salary}
              onChange={(e) => handleInputChange('salary', parseFloat(e.target.value))}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={loading}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Serviço (anos)</label>
            <input
              type="number"
              min="0"
              step="0.5"
              value={state.service_years}
              onChange={(e) => handleInputChange('service_years', parseFloat(e.target.value))}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={loading}
            />
          </div>
        </div>
      </div>

      {/* Parâmetros do Plano */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
          <Icon name="target" size="sm" className="text-gray-700" />
          Plano
        </h3>
        
        <SliderField
          label="Saldo Inicial"
          field="initial_balance"
          min={0}
          max={500000}
          step={5000}
          value={state.initial_balance}
          tooltip="Valor já acumulado"
          formatDisplay={(v) => `R$ ${(v/1000).toFixed(0)}k`}
        />

        <SliderField
          label="Benefício Desejado"
          field="target_benefit"
          min={1000}
          max={20000}
          step={100}
          value={state.target_benefit}
          tooltip="Valor mensal desejado"
          formatDisplay={(v) => `R$ ${(v/1000).toFixed(1)}k`}
        />

        <SliderField
          label="Taxa de Acumulação"
          field="accrual_rate"
          min={0}
          max={10}
          step={0.1}
          value={state.accrual_rate}
          suffix="%"
          formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
          tooltip="Rentabilidade real esperada"
        />

        <SliderField
          label="Idade Aposentadoria"
          field="retirement_age"
          min={state.age + 1}
          max={75}
          step={1}
          value={state.retirement_age}
          suffix=" anos"
          tooltip="Idade de aposentadoria"
        />

        <SliderField
          label="Taxa de Contribuição"
          field="contribution_rate"
          min={0}
          max={25}
          step={0.5}
          value={state.contribution_rate}
          suffix="%"
          formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
          tooltip="% do salário para contribuição"
        />
      </div>

      {/* Base Atuarial */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
          <Icon name="bar-chart" size="sm" className="text-gray-700" />
          Atuarial
        </h3>
        
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Tábua Mortalidade</label>
          <select
            value={state.mortality_table}
            onChange={(e) => handleInputChange('mortality_table', e.target.value)}
            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            disabled={loading}
          >
            {mortalityTables.map((table) => (
              <option key={table.code} value={table.code}>
                {table.code} {table.regulatory_approved && '✓'}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Desconto (%)</label>
            <input
              type="number"
              min="0"
              max="15"
              step="0.1"
              value={state.discount_rate * 100}
              onChange={(e) => handleInputChange('discount_rate', parseFloat(e.target.value) / 100)}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={loading}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Inflação (%)</label>
            <input
              type="number"
              min="0"
              max="15"
              step="0.1"
              value={state.inflation_rate * 100}
              onChange={(e) => handleInputChange('inflation_rate', parseFloat(e.target.value) / 100)}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={loading}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Sal. Real (%)</label>
            <input
              type="number"
              min="0"
              max="10"
              step="0.1"
              value={state.salary_growth_real * 100}
              onChange={(e) => handleInputChange('salary_growth_real', parseFloat(e.target.value) / 100)}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={loading}
            />
          </div>
        </div>
      </div>

      {/* Status */}
      {loading && (
        <div className="flex items-center justify-center py-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-xs text-gray-600">Calculando...</span>
        </div>
      )}
    </div>
  );
};

export default ParameterPanel;