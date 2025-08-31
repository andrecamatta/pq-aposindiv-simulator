import React from 'react';
import { DollarSign } from 'lucide-react';
import type { SimulatorState } from '../../types';
import { Card, CardHeader, CardTitle, CardContent, RangeSlider } from '../../design-system/components';
import { useFormHandler } from '../../hooks';

interface FinancialAssumptionsCardProps {
  state: SimulatorState;
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const FinancialAssumptionsCard: React.FC<FinancialAssumptionsCardProps> = ({ 
  state, 
  onStateChange, 
  loading 
}) => {
  const { handleInputChange } = useFormHandler({ onStateChange });

  return (
    <Card variant="default" padding="md">
      <CardHeader withBorder>
        <CardTitle className="flex items-center gap-3">
          <div className="w-10 h-10 bg-success-100 rounded-lg flex items-center justify-center">
            <DollarSign className="w-5 h-5 text-success-600" />
          </div>
          Premissas Financeiras
        </CardTitle>
      </CardHeader>
      
      <CardContent className="pt-6">
        <div className="space-y-6">
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
            suffix="%"
            tooltip="Percentual do salário destinado à contribuição mensal"
            disabled={loading}
          />
          
          <RangeSlider
            label="Taxa de Acumulação Real"
            value={state.accrual_rate}
            min={0}
            max={12}
            step={0.1}
            onChange={(value) => handleInputChange('accrual_rate', value)}
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
            formatDisplay={(v) => `${(v * 100).toFixed(1)}`}
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
            formatDisplay={(v) => `${(v * 100).toFixed(1)}`}
            disabled={loading}
          />
        </div>
      </CardContent>
    </Card>
  );
};

export default FinancialAssumptionsCard;