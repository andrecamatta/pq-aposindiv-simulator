import React, { useMemo, useCallback } from 'react';
import { Settings } from 'lucide-react';
import type { SimulatorState, MortalityTable, PaymentTiming, PlanType, CDConversionMode } from '../../types';
import { Card, CardHeader, CardTitle, CardContent, Select, RangeSlider } from '../../design-system/components';
import { formatSimplePercentageBR } from '../../utils/formatBR';
import { useFormHandler } from '../../hooks';

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


  return (
    <Card className="border-gray-200">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-xl">
          <Settings className="w-5 h-5 text-gray-600" />
          <span>Configurações Técnicas</span>
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-8">
          {/* Tipo de Plano */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Tipo de Plano</h4>
            <div className="grid md:grid-cols-1 gap-8">
              <Select
                label={
                  <span title="BD (Benefício Definido): benefício garantido, contribuição variável. CD (Contribuição Definida): contribuição fixa, benefício baseado no saldo acumulado.">
                    Tipo de Plano
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
            <div className="grid md:grid-cols-2 gap-8">
              {/* Modalidade de Benefício - sempre presente */}
              <Select
                label={
                  <span title={state.plan_type === 'CD' ? "Como converter o saldo acumulado em renda na aposentadoria." : "Escolha como definir o benefício desejado. Valor fixo especifica um valor em reais, enquanto taxa de reposição especifica um percentual do salário final."}>
                    {state.plan_type === 'CD' ? 'Modalidade de Conversão' : 'Modalidade de Benefício'}
                  </span>
                }
                value={state.plan_type === 'CD' ? (state.cd_conversion_mode || 'ACTUARIAL') : (state.benefit_target_mode || 'VALUE')}
                onChange={(value) => handleInputChange(state.plan_type === 'CD' ? 'cd_conversion_mode' : 'benefit_target_mode', value)}
                options={state.plan_type === 'CD' ? cdConversionOptions : benefitModeOptions}
                disabled={loading}
              />

              <Select
                label={
                  <span title="Define probabilidades de sobrevivência. BR_EMS_2021 é conservadora e adequada ao mercado brasileiro.">
                    Tábua de Mortalidade
                  </span>
                }
                value={state.mortality_table || 'BR_EMS_2021'}
                onChange={(value) => handleInputChange('mortality_table', value)}
                options={mortalityOptions}
                disabled={loading}
              />
            </div>

            
            <div className="mt-6">
              <RangeSlider
                label={
                  <span title="Margem de segurança atuarial. Valores positivos tornam o cálculo mais conservador, negativos menos conservador. Padrão de mercado SUSEP.">
                    Agravamento da Tábua
                  </span>
                }
                value={state.mortality_aggravation || 0}
                min={-10}
                max={20}
                step={1}
                onChange={(value) => handleInputChange('mortality_aggravation', value)}
                formatDisplay={(v) => `${v > 0 ? '+' : ''}${v.toFixed(0)}%`}
                disabled={loading}
              />
            </div>
          </div>

          {/* Custos Administrativos */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Custos Administrativos</h4>
            <div className="grid md:grid-cols-2 gap-8">
              <RangeSlider
                label={
                  <span title="Taxa administrativa anual cobrada sobre o saldo acumulado. Aplicada mensalmente.">
                    Taxa Anual sobre Saldo
                  </span>
                }
                value={(state.admin_fee_rate ?? 0.01) * 100}
                min={0}
                max={3}
                step={0.1}
                onChange={handleAdminFeeChange}
                formatDisplay={(v) => formatSimplePercentageBR(v, 2)}
                disabled={loading}
              />
              
              <RangeSlider
                label={
                  <span title="Percentual descontado das contribuições antes de serem aplicadas ao saldo.">
                    Taxa de Carregamento
                  </span>
                }
                value={(state.loading_fee_rate ?? 0) * 100}
                min={0}
                max={15}
                step={0.5}
                onChange={handleLoadingFeeChange}
                formatDisplay={(v) => formatSimplePercentageBR(v, 2)}
                disabled={loading}
              />
            </div>
          </div>

          {/* Configurações de Pagamento */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Configurações de Pagamento</h4>
            <div className="grid md:grid-cols-3 gap-8">
              <Select
                label={
                  <span title="Antecipado: pagamentos no início do período. Postecipado: pagamentos no final do período.">
                    Timing de Pagamento
                  </span>
                }
                value={state.payment_timing || 'postecipado'}
                onChange={(value) => handleInputChange('payment_timing', value)}
                options={timingOptions}
                disabled={loading}
              />

              <Select
                label={
                  <span title="Quantidade de salários pagos por ano (inclui 13º, 14º salário).">
                    Salários por Ano
                  </span>
                }
                value={state.salary_months_per_year || 13}
                onChange={(value) => handleInputChange('salary_months_per_year', parseInt(value))}
                options={monthsOptions}
                disabled={loading}
              />

              <Select
                label={
                  <span title="Quantidade de benefícios pagos por ano na aposentadoria (inclui 13º, 14º).">
                    Benefícios por Ano
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