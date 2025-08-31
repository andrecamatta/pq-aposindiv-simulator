import React, { useMemo, useCallback } from 'react';
import { Settings } from 'lucide-react';
import type { SimulatorState, MortalityTable, PaymentTiming } from '../../types';
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
        <div className="space-y-6">
          {/* Configurações Atuariais */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-4">Configurações Atuariais</h4>
            <div className="grid md:grid-cols-2 gap-6">
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
                value={(state.admin_fee_rate || 0.01) * 100}
                min={0}
                max={3}
                step={0.1}
                onChange={handleAdminFeeChange}
                formatDisplay={(v) => `${v.toFixed(1)}%`}
                disabled={loading}
              />
              
              <RangeSlider
                label={
                  <span className="flex items-center gap-2">
                    Taxa de Carregamento
                    <InfoTooltip content="Percentual descontado das contribuições antes de serem aplicadas ao saldo." />
                  </span>
                }
                value={(state.loading_fee_rate || 0) * 100}
                min={0}
                max={15}
                step={0.5}
                onChange={handleLoadingFeeChange}
                formatDisplay={(v) => `${v.toFixed(1)}%`}
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
                onChange={(e) => handleInputChange('payment_timing', e.target.value)}
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
                onChange={(e) => handleInputChange('salary_months_per_year', parseInt(e.target.value))}
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
                onChange={(e) => handleInputChange('benefit_months_per_year', parseInt(e.target.value))}
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