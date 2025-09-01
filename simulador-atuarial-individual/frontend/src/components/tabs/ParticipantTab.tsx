import React from 'react';
import { User } from 'lucide-react';
import type { SimulatorState } from '../../types';
import { Input, Select, CurrencyInput, RangeSlider } from '../../design-system/components';
import InfoTooltip from '../../design-system/components/InfoTooltip';
import { formatCurrencyBR } from '../../utils/formatBR';
import { useFormHandler } from '../../hooks';

interface ParticipantTabProps {
  state: SimulatorState;
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const ParticipantTab: React.FC<ParticipantTabProps> = ({ 
  state, 
  onStateChange, 
  loading 
}) => {
  const { handleInputChange } = useFormHandler({ onStateChange });

  const genderOptions = [
    { value: 'M', label: 'Masculino' },
    { value: 'F', label: 'Feminino' }
  ];

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3 mb-2">
          <User className="w-6 h-6 text-blue-600" />
          Dados do Participante
        </h1>
        <p className="text-gray-600">Configure as informações pessoais e financeiras do participante.</p>
      </div>
      
      <div className="bg-white rounded-xl shadow-sm p-8">
        <div className="grid md:grid-cols-2 gap-6">
          {/* Coluna 1: Dados Pessoais */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">
              Informações Pessoais
            </h3>
            
            <Input
              label={
                <span className="flex items-center gap-2">
                  Idade Atual
                  <InfoTooltip content="Sua idade atual. A simulação projeta até os 100 anos." />
                </span>
              }
              type="number"
              value={state.age || ''}
              onChange={(e) => handleInputChange('age', parseInt(e.target.value) || 0)}
              placeholder="35"
              min={18}
              max={80}
              disabled={loading}
            />
            
            <Select
              label={
                <span className="flex items-center gap-2">
                  Gênero
                  <InfoTooltip content="Afeta as probabilidades de sobrevivência conforme tábuas atuariais." />
                </span>
              }
              value={state.gender}
              onChange={(e) => handleInputChange('gender', e.target.value)}
              options={genderOptions}
              disabled={loading}
            />
          </div>

          {/* Coluna 2: Dados Financeiros */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">
              Informações Financeiras
            </h3>
            
            <RangeSlider
              label={
                <span className="flex items-center gap-2">
                  Salário Mensal
                  <InfoTooltip content="Base para cálculo de contribuições e benefícios futuros." />
                </span>
              }
              value={state.salary || 10000}
              min={0}
              max={100000}
              step={1000}
              onChange={(value) => handleInputChange('salary', value)}
              formatDisplay={(v) => formatCurrencyBR(v, 2)}
              disabled={loading}
            />
            
            <RangeSlider
              label={
                <span className="flex items-center gap-2">
                  Saldo Inicial
                  <InfoTooltip content="Valor já acumulado no plano de previdência." />
                </span>
              }
              value={state.initial_balance || 0}
              min={0}
              max={2000000}
              step={10000}
              onChange={(value) => handleInputChange('initial_balance', value)}
              formatDisplay={(v) => formatCurrencyBR(v, 2)}
              disabled={loading}
            />
            
            <RangeSlider
              label={
                <span className="flex items-center gap-2">
                  Crescimento Salarial Real
                  <InfoTooltip content="Crescimento real anual esperado do seu salário (já descontada a inflação)." />
                </span>
              }
              value={state.salary_growth_real || 0.02}
              min={0}
              max={0.10}
              step={0.001}
              onChange={(value) => handleInputChange('salary_growth_real', value)}
              formatDisplay={(v) => (v * 100).toFixed(2).replace('.', ',')}
              suffix="%"
              disabled={loading}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ParticipantTab;
