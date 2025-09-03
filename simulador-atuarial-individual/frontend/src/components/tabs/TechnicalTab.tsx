import React, { useMemo, useCallback } from 'react';
import { Settings } from 'lucide-react';
import type { SimulatorState, MortalityTable, PaymentTiming, PlanType, CDConversionMode } from '../../types';
import { Card, CardHeader, CardTitle, CardContent, Select, RangeSlider } from '../../design-system/components';
import { useFormHandler } from '../../hooks';
import InfoTooltip from '../../design-system/components/InfoTooltip';

interface TechnicalTabProps {
  state: SimulatorState;
  mortalityTables: MortalityTable[];
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const TechnicalTab: React.FC<TechnicalTabProps> = React.memo(({ 
  state, 
  mortalityTables,
  onStateChange, 
  loading 
}) => {
  const { handleInputChange } = useFormHandler({ onStateChange });

  // Memoizar opções para evitar recriação desnecessária
  const mortalityOptions = useMemo(() => 
    mortalityTables.map(table => ({
      value: table.code,
      label: table.name
    })), [mortalityTables]
  );

  const methodOptions = useMemo(() => [
    { value: 'PUC', label: 'PUC - Projected Unit Credit' },
    { value: 'EAN', label: 'EAN - Entry Age Normal' }
  ], []);

  const timingOptions = useMemo(() => [
    { value: 'postecipado', label: 'Postecipado (final do período)' },
    { value: 'antecipado', label: 'Antecipado (início do período)' }
  ], []);

  const monthsOptions = useMemo(() => [
    { value: 12, label: '12 meses' },
    { value: 13, label: '13 meses (13º)' },
    { value: 14, label: '14 meses (13º + 14º)' }
  ], []);

  const planTypeOptions = useMemo(() => [
    { value: 'BD', label: 'BD - Benefício Definido' },
    { value: 'CD', label: 'CD - Contribuição Definida' }
  ], []);

  const benefitModeOptions = useMemo(() => [
    { value: 'VALUE', label: 'Valor Fixo (R$)' },
    { value: 'REPLACEMENT_RATE', label: 'Taxa de Reposição (%)' }
  ], []);

  const cdConversionOptions = useMemo(() => [
    { value: 'ACTUARIAL', label: 'Cálculo Atuarial (Vitalícia)' },
    { value: 'CERTAIN_5Y', label: 'Renda Certa por 5 anos' },
    { value: 'CERTAIN_10Y', label: 'Renda Certa por 10 anos' },
    { value: 'CERTAIN_15Y', label: 'Renda Certa por 15 anos' },
    { value: 'CERTAIN_20Y', label: 'Renda Certa por 20 anos' },
    { value: 'PERCENTAGE', label: 'Percentual do Saldo' },
    { value: 'PROGRAMMED', label: 'Saque Programado' }
  ], []);

  // Memoizar handlers específicos para evitar re-renders
  const handleAdminFeeChange = useCallback((value: number) => {
    handleInputChange('admin_fee_rate', value / 100);
  }, [handleInputChange]);

  const handleLoadingFeeChange = useCallback((value: number) => {
    handleInputChange('loading_fee_rate', value / 100);
  }, [handleInputChange]);

  const handleAccumulationRateChange = useCallback((value: number) => {
    handleInputChange('accumulation_rate', value / 100);
  }, [handleInputChange]);

  const handleConversionRateChange = useCallback((value: number) => {
    handleInputChange('conversion_rate', value / 100);
  }, [handleInputChange]);

  const handleDiscountRateChange = useCallback((value: number) => {
    handleInputChange('discount_rate', value / 100);
  }, [handleInputChange]);

  const handleSalaryGrowthChange = useCallback((value: number) => {
    handleInputChange('salary_growth_real', value / 100);
  }, [handleInputChange]);

  const handleWithdrawalPercentageChange = useCallback((value: number) => {
    handleInputChange('cd_withdrawal_percentage', value);
  }, [handleInputChange]);

  return (
    <Card className="border-gray-200">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-xl">
          <Settings className="w-5 h-5 text-gray-600" />
          <span>Configurações Técnicas</span>
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-6">
          {/* Tipo de Plano */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Tipo de Plano</h4>
            <div className="grid md:grid-cols-1 gap-6">
              <Select
                label={
                  <span className="flex items-center gap-2">
                    Tipo de Plano
                    <InfoTooltip content="BD (Benefício Definido): benefício garantido, contribuição variável. CD (Contribuição Definida): contribuição fixa, benefício baseado no saldo acumulado." />
                  </span>
                }
                value={state.plan_type || 'BD'}
                onChange={(value) => handleInputChange('plan_type', value)}
                options={planTypeOptions}
                disabled={loading}
              />
            </div>
          </div>

          {/* Configurações Atuariais */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Configurações Atuariais</h4>
            <div className="grid md:grid-cols-2 gap-6">
              {/* Modalidade de Benefício - sempre presente */}
              <Select
                label={
                  <span className="flex items-center gap-2">
                    {state.plan_type === 'CD' ? 'Modalidade de Conversão' : 'Modalidade de Benefício'}
                    <InfoTooltip content={
                      state.plan_type === 'CD' 
                        ? "Como converter o saldo acumulado em renda na aposentadoria."
                        : "Escolha como definir o benefício desejado. Valor fixo especifica um valor em reais, enquanto taxa de reposição especifica um percentual do salário final."
                    } />
                  </span>
                }
                value={state.plan_type === 'CD' ? (state.cd_conversion_mode || 'ACTUARIAL') : (state.benefit_target_mode || 'VALUE')}
                onChange={(value) => handleInputChange(state.plan_type === 'CD' ? 'cd_conversion_mode' : 'benefit_target_mode', value)}
                options={state.plan_type === 'CD' ? cdConversionOptions : benefitModeOptions}
                disabled={loading}
              />

              <Select
                label={
                  <span className="flex items-center gap-2">
                    Tábua de Mortalidade
                    <InfoTooltip content="Define probabilidades de sobrevivência. BR_EMS_2021 é conservadora e adequada ao mercado brasileiro." />
                  </span>
                }
                value={state.mortality_table || 'BR_EMS_2021'}
                onChange={(e) => handleInputChange('mortality_table', e.target.value)}
                options={mortalityOptions}
                disabled={loading}
              />
            </div>

            {/* Configurações específicas por tipo de plano */}
            <div className="grid md:grid-cols-2 gap-6 mt-6">
              {state.plan_type === 'BD' ? (
                <>
                  {/* Configurações BD */}
                  <div>
                    <RangeSlider
                      label={
                        <span className="flex items-center gap-2">
                          Taxa de Desconto
                          <InfoTooltip content="Taxa utilizada para trazer valores futuros a valor presente. Representa o retorno esperado dos investimentos." />
                        </span>
                      }
                      value={(state.discount_rate || 0.055) * 100}
                      min={3}
                      max={12}
                      step={0.1}
                      onChange={handleDiscountRateChange}
                      formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
                      suffix="% a.a."
                      disabled={loading}
                    />
                  </div>
                  <div>
                    <RangeSlider
                      label={
                        <span className="flex items-center gap-2">
                          Taxa Crescimento Salarial Real
                          <InfoTooltip content="Taxa de crescimento real dos salários (acima da inflação). Considera ganhos de produtividade e progressão de carreira." />
                        </span>
                      }
                      value={(state.salary_growth_real || 0.025) * 100}
                      min={0}
                      max={6}
                      step={0.1}
                      onChange={handleSalaryGrowthChange}
                      formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
                      suffix="% a.a."
                      disabled={loading}
                    />
                  </div>
                  <div>
                    <Select
                      label={
                        <span className="flex items-center gap-2">
                          Método de Cálculo
                          <InfoTooltip content="PUC: custos crescentes ao longo do tempo. EAN: custos uniformes durante a carreira." />
                        </span>
                      }
                      value={state.calculation_method || 'PUC'}
                      onChange={(e) => handleInputChange('calculation_method', e.target.value)}
                      options={methodOptions}
                      disabled={loading}
                    />
                  </div>
                </>
              ) : (
                <>
                  {/* Configurações CD */}
                  <div>
                    <RangeSlider
                      label={
                        <span className="flex items-center gap-2">
                          Taxa de Acumulação
                          <InfoTooltip content="Taxa de retorno dos investimentos durante a fase de acumulação (antes da aposentadoria)." />
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
                  </div>
                  <div>
                    <RangeSlider
                      label={
                        <span className="flex items-center gap-2">
                          Taxa de Conversão
                          <InfoTooltip content="Taxa utilizada para converter o saldo acumulado em renda na aposentadoria. Geralmente mais conservadora." />
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
                  </div>
                  <div>
                    <RangeSlider
                      label={
                        <span className="flex items-center gap-2">
                          Taxa Crescimento Salarial Real
                          <InfoTooltip content="Taxa de crescimento real dos salários (acima da inflação). Afeta as contribuições futuras." />
                        </span>
                      }
                      value={(state.salary_growth_real || 0.025) * 100}
                      min={0}
                      max={6}
                      step={0.1}
                      onChange={handleSalaryGrowthChange}
                      formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
                      suffix="% a.a."
                      disabled={loading}
                    />
                  </div>
                  
                  {/* Campo condicional para modalidade PERCENTAGE */}
                  {state.cd_conversion_mode === 'PERCENTAGE' && (
                    <div>
                      <RangeSlider
                        label={
                          <span className="flex items-center gap-2">
                            Percentual de Saque Anual
                            <InfoTooltip content="Percentual do saldo que será sacado anualmente na aposentadoria." />
                          </span>
                        }
                        value={state.cd_withdrawal_percentage || 5}
                        min={2}
                        max={15}
                        step={0.5}
                        onChange={handleWithdrawalPercentageChange}
                        formatDisplay={(v) => v.toFixed(1).replace('.', ',')}
                        suffix="% a.a."
                        disabled={loading}
                      />
                    </div>
                  )}
                </>
              )}
            </div>
            
            <div className="mt-6">
              <RangeSlider
                label={
                  <span className="flex items-center gap-2">
                    Agravamento da Tábua
                    <InfoTooltip content="Margem de segurança atuarial. Valores positivos tornam o cálculo mais conservador, negativos menos conservador. Padrão de mercado SUSEP." />
                  </span>
                }
                value={state.mortality_aggravation || 0}
                min={-10}
                max={20}
                step={1}
                onChange={(value) => handleInputChange('mortality_aggravation', value)}
                formatDisplay={(v) => v > 0 ? `+${v.toFixed(0)}` : `${v.toFixed(0)}`}
                suffix="%"
                disabled={loading}
              />
            </div>
          </div>

          {/* Custos Administrativos */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Custos Administrativos</h4>
            <div className="grid md:grid-cols-2 gap-6">
              <RangeSlider
                label={
                  <span className="flex items-center gap-2">
                    Taxa Anual sobre Saldo
                    <InfoTooltip content="Taxa administrativa anual cobrada sobre o saldo acumulado. Aplicada mensalmente." />
                  </span>
                }
                value={(state.admin_fee_rate ?? 0.01) * 100}
                min={0}
                max={3}
                step={0.1}
                onChange={handleAdminFeeChange}
                formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
                suffix="%"
                disabled={loading}
              />
              
              <RangeSlider
                label={
                  <span className="flex items-center gap-2">
                    Taxa de Carregamento
                    <InfoTooltip content="Percentual descontado das contribuições antes de serem aplicadas ao saldo." />
                  </span>
                }
                value={(state.loading_fee_rate ?? 0) * 100}
                min={0}
                max={15}
                step={0.5}
                onChange={handleLoadingFeeChange}
                formatDisplay={(v) => v.toFixed(2).replace('.', ',')}
                suffix="%"
                disabled={loading}
              />
            </div>
          </div>

          {/* Configurações de Pagamento */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Configurações de Pagamento</h4>
            <div className="grid md:grid-cols-3 gap-6">
              <Select
                label={
                  <span className="flex items-center gap-2">
                    Timing de Pagamento
                    <InfoTooltip content="Antecipado: pagamentos no início do período. Postecipado: pagamentos no final do período." />
                  </span>
                }
                value={state.payment_timing || 'postecipado'}
                onChange={(value) => handleInputChange('payment_timing', value)}
                options={timingOptions}
                disabled={loading}
              />

              <Select
                label={
                  <span className="flex items-center gap-2">
                    Salários por Ano
                    <InfoTooltip content="Quantidade de salários pagos por ano (inclui 13º, 14º salário)." />
                  </span>
                }
                value={state.salary_months_per_year || 13}
                onChange={(value) => handleInputChange('salary_months_per_year', parseInt(value))}
                options={monthsOptions}
                disabled={loading}
              />

              <Select
                label={
                  <span className="flex items-center gap-2">
                    Benefícios por Ano
                    <InfoTooltip content="Quantidade de benefícios pagos por ano na aposentadoria (inclui 13º, 14º)." />
                  </span>
                }
                value={state.benefit_months_per_year || 13}
                onChange={(value) => handleInputChange('benefit_months_per_year', parseInt(value))}
                options={monthsOptions}
                disabled={loading}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
});

TechnicalTab.displayName = 'TechnicalTab';

export default TechnicalTab;