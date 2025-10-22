import { useCallback } from 'react';
import type { SimulatorState } from '../../../types';
import { RangeSlider } from '../../../design-system/components';
import { formatSimplePercentageBR } from '../../../utils/formatBR';
import { useFormHandler } from '../../../hooks';

interface AssumptionsFinancialViewProps {
  state: SimulatorState;
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const AssumptionsFinancialView: React.FC<AssumptionsFinancialViewProps> = ({
  state,
  onStateChange,
  loading
}) => {
  const { handleInputChange } = useFormHandler({ onStateChange });

  // Handlers para taxas
  const handleDiscountRateChange = useCallback((value: number) => {
    handleInputChange('discount_rate', value / 100);
  }, [handleInputChange]);

  const handleAccumulationRateChange = useCallback((value: number) => {
    handleInputChange('accumulation_rate', value / 100);
  }, [handleInputChange]);

  const handleConversionRateChange = useCallback((value: number) => {
    handleInputChange('conversion_rate', value / 100);
  }, [handleInputChange]);

  return (
    <div className="bg-white rounded-xl shadow-sm p-8">
      <div className="space-y-12">
        {/* Benefícios e Contribuições */}
        <div className="space-y-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">
            Benefícios & Contribuições
          </h3>

          {/* Campo de benefício desejado - não mostra para modalidade PERCENTAGE em CD */}
          {!(state.plan_type === 'CD' && state.cd_conversion_mode === 'PERCENTAGE') && (
            <>
              {state.benefit_target_mode === 'VALUE' ? (
                <RangeSlider
                  label={
                    <span title="Valor mensal desejado de aposentadoria em reais.">
                      Benefício Mensal Desejado
                    </span>
                  }
                  value={state.target_benefit || 8000}
                  min={1000}
                  max={50000}
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
                  formatDisplay={(v) => formatSimplePercentageBR(v, 2)}
                  disabled={loading}
                />
              )}
            </>
          )}

          {/* Campo condicional para modalidade PERCENTAGE em CD */}
          {state.plan_type === 'CD' && state.cd_conversion_mode === 'PERCENTAGE' && (
            <>
              <RangeSlider
                label={
                  <span title="Percentual do saldo que será sacado anualmente na aposentadoria.">
                    Percentual de Saque Anual
                  </span>
                }
                value={state.cd_withdrawal_percentage || 8}
                min={2}
                max={15}
                step={0.5}
                onChange={(value) => handleInputChange('cd_withdrawal_percentage', value)}
                formatDisplay={(v) => formatSimplePercentageBR(v, 1)}
                suffix=" a.a."
                disabled={loading}
              />

              <RangeSlider
                label={
                  <span title="Crescimento anual do percentual de saque para compensar expectativa de vida reduzida.">
                    Crescimento Anual do Saque
                  </span>
                }
                value={state.cd_percentage_growth || 0.1}
                min={0}
                max={0.25}
                step={0.01}
                onChange={(value) => handleInputChange('cd_percentage_growth', value)}
                formatDisplay={(v) => formatSimplePercentageBR(v, 2)}
                suffix=" a.a."
                disabled={loading}
              />
            </>
          )}

          {/* Campo condicional para modalidade ACTUARIAL_EQUIVALENT em CD */}
          {state.plan_type === 'CD' && state.cd_conversion_mode === 'ACTUARIAL_EQUIVALENT' && (
            <RangeSlider
              label={
                <span title="Percentual mínimo do benefício inicial que será mantido como piso de renda.">
                  Piso de Renda (% do 1º Ano)
                </span>
              }
              value={state.cd_floor_percentage || 70}
              min={50}
              max={100}
              step={5}
              onChange={(value) => handleInputChange('cd_floor_percentage', value)}
              formatDisplay={(v) => formatSimplePercentageBR(v, 0)}
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
            value={state.contribution_rate || 12}
            min={0}
            max={25}
            step={0.5}
            onChange={(value) => handleInputChange('contribution_rate', value)}
            formatDisplay={(v) => formatSimplePercentageBR(v, 2)}
            disabled={loading}
          />
        </div>

        {/* Taxas de Rentabilidade - Taxas diferenciadas para BD e CD */}
        <div className="space-y-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">
            Taxas de Rentabilidade
          </h3>

          {/* BD: Taxa Atuarial única | CD: Taxas separadas de acumulação e conversão */}
          {state.plan_type === 'BD' ? (
            // BD usa apenas taxa atuarial (discount_rate)
            <RangeSlider
              label={
                <span title="Taxa de desconto atuarial única usada para cálculo de benefícios e contribuições em planos BD.">
                  Taxa Atuarial
                </span>
              }
              value={(state.discount_rate || 0.05) * 100}
              min={0}
              max={7}
              step={0.1}
              onChange={handleDiscountRateChange}
              formatDisplay={(v) => `${formatSimplePercentageBR(v, 2)} a.a.`}
              disabled={loading}
            />
          ) : (
            // CD usa taxas separadas de acumulação e conversão
            <>
              <RangeSlider
                label={
                  <span title="Taxa de retorno dos investimentos durante a fase de acumulação (antes da aposentadoria).">
                    Taxa de Acumulação
                  </span>
                }
                value={(state.accumulation_rate || state.discount_rate || 0.05) * 100}
                min={0}
                max={7}
                step={0.1}
                onChange={handleAccumulationRateChange}
                formatDisplay={(v) => `${formatSimplePercentageBR(v, 2)} a.a.`}
                disabled={loading}
              />

              <RangeSlider
                label={
                  <span title="Taxa utilizada para cálculo atuarial de benefícios e conversão em renda. Geralmente mais conservadora.">
                    Taxa de Conversão
                  </span>
                }
                value={(state.conversion_rate || state.discount_rate || 0.04) * 100}
                min={0}
                max={7}
                step={0.1}
                onChange={handleConversionRateChange}
                formatDisplay={(v) => `${formatSimplePercentageBR(v, 2)} a.a.`}
                disabled={loading}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssumptionsFinancialView;
