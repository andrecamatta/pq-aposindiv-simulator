import React, { useCallback } from 'react';
import type { SimulatorState } from '../../types';
import { RangeSlider, Select } from '../../design-system/components';
import { useFormHandler } from '../../hooks';

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

  // Handlers para taxas CD
  const handleAccumulationRateChange = useCallback((value: number) => {
    handleInputChange('accumulation_rate', value / 100);
  }, [handleInputChange]);

  const handleConversionRateChange = useCallback((value: number) => {
    handleInputChange('conversion_rate', value / 100);
  }, [handleInputChange]);

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#111618] mb-2">
          Premissas Financeiras
        </h1>
        <p className="text-[#617c89]">Configure as premissas atuariais e financeiras para a simulação.</p>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm p-8">
        <div className="space-y-12">
          {/* Benefícios e Contribuições */}
          <div className="space-y-8">
            <h3 className="text-lg font-semibold text-[#111618] mb-6">
              Benefícios & Contribuições
            </h3>
            
            {state.benefit_target_mode === 'VALUE' ? (
              <RangeSlider
                label={
                  <span title="Valor mensal desejado de aposentadoria em reais.">
                    Benefício Mensal Desejado
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
                  <span title="Percentual do salário final que deseja receber como benefício.">
                    Taxa de Reposição Desejada
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
                <span title="Idade planejada para início dos benefícios de aposentadoria.">
                  Idade de Aposentadoria
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
                <span title="Percentual do salário destinado à contribuição mensal.">
                  Taxa de Contribuição
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

          {/* Taxas de Rentabilidade - Condicionais por Tipo de Plano */}
          <div className="space-y-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">
              Taxas de Rentabilidade
            </h3>
            
            {state.plan_type === 'CD' ? (
              // Taxas específicas para CD
              <>
                <RangeSlider
                  label={
                    <span title="Taxa de retorno dos investimentos durante a fase de acumulação (antes da aposentadoria).">
                      Taxa de Acumulação
                    </span>
                  }
                  value={(state.accumulation_rate || 0.065) * 100}
                  min={3}
                  max={15}
                  step={0.1}
                  onChange={handleAccumulationRateChange}
                  formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
                  suffix="% a.a."
                  disabled={loading}
                />
                
                <RangeSlider
                  label={
                    <span title="Taxa utilizada para converter o saldo acumulado em renda na aposentadoria. Geralmente mais conservadora.">
                      Taxa de Conversão
                    </span>
                  }
                  value={(state.conversion_rate || 0.045) * 100}
                  min={2}
                  max={10}
                  step={0.1}
                  onChange={handleConversionRateChange}
                  formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
                  suffix="% a.a."
                  disabled={loading}
                />
              </>
            ) : (
              // Taxas BD - Mantém funcionamento original
              <>
                <RangeSlider
                  label={
                    <span title="Rentabilidade real anual esperada dos investimentos (já descontada a inflação).">
                      Taxa de Acumulação Real
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
                    <span title="Taxa real usada para calcular o valor presente das obrigações.">
                      Taxa de Desconto Real
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
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssumptionsTab;
