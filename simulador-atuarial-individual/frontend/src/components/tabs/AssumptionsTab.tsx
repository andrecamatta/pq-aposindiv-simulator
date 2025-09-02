import React from 'react';
import { Settings } from 'lucide-react';
import type { SimulatorState } from '../../types';
import { RangeSlider, Select } from '../../design-system/components';
import { useFormHandler } from '../../hooks';
import InfoTooltip from '../../design-system/components/InfoTooltip';

interface AssumptionsTabProps {
  state: SimulatorState;
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const AssumptionsTab: React.FC<AssumptionsTabProps> = ({ 
  state, 
  onStateChange, 
  loading 
}) => {
  const { handleInputChange } = useFormHandler({ onStateChange });

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3 mb-2">
          <Settings className="w-6 h-6 text-violet-600" />
          Premissas Financeiras
        </h1>
        <p className="text-gray-600">Configure as premissas atuariais e financeiras para a simulação.</p>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm p-8">
        <div className="space-y-10">
          {/* Benefícios e Contribuições */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">
              Benefícios & Contribuições
            </h3>
            
            {state.benefit_target_mode === 'VALUE' ? (
              <RangeSlider
                label={
                  <span className="flex items-center gap-2">
                    Benefício Mensal Desejado
                    <InfoTooltip content="Valor mensal desejado de aposentadoria em reais." />
                  </span>
                }
                value={state.target_benefit || 5000}
                min={1000}
                max={100000}
                step={1000}
                onChange={(value) => handleInputChange('target_benefit', value)}
                formatDisplay={(v) => `R$ ${new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(v)}`}
                disabled={loading}
              />
            ) : (
              <RangeSlider
                label={
                  <span className="flex items-center gap-2">
                    Taxa de Reposição Desejada
                    <InfoTooltip content="Percentual do salário final que deseja receber como benefício." />
                  </span>
                }
                value={state.target_replacement_rate || 70}
                min={30}
                max={100}
                step={5}
                onChange={(value) => handleInputChange('target_replacement_rate', value)}
                formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
                suffix="%"
                disabled={loading}
              />
            )}
            
            <RangeSlider
              label={
                <span className="flex items-center gap-2">
                  Idade de Aposentadoria
                  <InfoTooltip content="Idade planejada para início dos benefícios de aposentadoria." />
                </span>
              }
              value={state.retirement_age || 65}
              min={Math.max(55, (state.age || 30) + 5)}
              max={75}
              step={1}
              onChange={(value) => handleInputChange('retirement_age', value)}
              suffix=" anos"
              disabled={loading}
            />
            
            <RangeSlider
              label={
                <span className="flex items-center gap-2">
                  Taxa de Contribuição
                  <InfoTooltip content="Percentual do salário destinado à contribuição mensal." />
                </span>
              }
              value={state.contribution_rate || 8}
              min={0}
              max={25}
              step={0.5}
              onChange={(value) => handleInputChange('contribution_rate', value)}
              formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
              suffix="%"
              disabled={loading}
            />
          </div>

          {/* Taxas de Rentabilidade */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">
              Taxas de Rentabilidade
            </h3>
            
            <RangeSlider
              label={
                <span className="flex items-center gap-2">
                  Taxa de Acumulação Real
                  <InfoTooltip content="Rentabilidade real anual esperada dos investimentos (já descontada a inflação)." />
                </span>
              }
              value={state.accrual_rate || 5}
              min={0}
              max={12}
              step={0.1}
              onChange={(value) => handleInputChange('accrual_rate', value)}
              formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
              suffix="%"
              disabled={loading}
            />
            
            <RangeSlider
              label={
                <span className="flex items-center gap-2">
                  Taxa de Desconto Real
                  <InfoTooltip content="Taxa real usada para calcular o valor presente das obrigações." />
                </span>
              }
              value={state.discount_rate ? state.discount_rate * 100 : 4}
              min={0}
              max={12}
              step={0.1}
              onChange={(value) => handleInputChange('discount_rate', value / 100)}
              formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
              suffix="%"
              disabled={loading}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssumptionsTab;
