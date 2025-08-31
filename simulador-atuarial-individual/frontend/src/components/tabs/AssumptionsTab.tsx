import React from 'react';
import { Settings } from 'lucide-react';
import type { SimulatorState } from '../../types';
import { Card, CardHeader, CardTitle, CardContent, RangeSlider, Select } from '../../design-system/components';
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
    <Card className="border-gray-200">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-xl">
          <Settings className="w-5 h-5 text-gray-600" />
          <span>Premissas Financeiras</span>
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-6">
          {/* Benefícios e Contribuições */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
              Benefícios & Contribuições
            </h3>
            
            <Select
              label={
                <span className="flex items-center gap-2">
                  Modalidade de Benefício
                  <InfoTooltip content="Escolha como definir o benefício desejado. Valor fixo especifica um valor em reais, enquanto taxa de reposição especifica um percentual do salário final." />
                </span>
              }
              value={state.benefit_target_mode || 'VALUE'}
              onChange={(e) => handleInputChange('benefit_target_mode', e.target.value)}
              options={[
                { value: 'VALUE', label: 'Valor Fixo (R$)' },
                { value: 'REPLACEMENT_RATE', label: 'Taxa de Reposição (%)' }
              ]}
              disabled={loading}
            />
            
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
                formatDisplay={(v) => `R$ ${new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 0 }).format(v)}`}
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
              suffix="%"
              disabled={loading}
            />
          </div>

          {/* Taxas de Rentabilidade */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
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
              suffix="%"
              disabled={loading}
            />
          </div>

          {/* Crescimento Temporal */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
              Crescimento no Tempo
            </h3>
            
            <RangeSlider
              label={
                <span className="flex items-center gap-2">
                  Crescimento Salarial Real
                  <InfoTooltip content="Crescimento real anual dos salários (já descontada a inflação)." />
                </span>
              }
              value={state.salary_growth_real || 0.02}
              min={0}
              max={0.10}
              step={0.001}
              onChange={(value) => handleInputChange('salary_growth_real', value)}
              suffix="%"
              formatDisplay={(v) => `${(v * 100).toFixed(1)}`}
              disabled={loading}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AssumptionsTab;
