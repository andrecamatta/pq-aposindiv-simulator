import React from 'react';
import { User } from 'lucide-react';
import type { SimulatorState } from '../../types';
import { Card, CardHeader, CardTitle, CardContent, Input, Select, CurrencyInput } from '../../design-system/components';
import InfoTooltip from '../../design-system/components/InfoTooltip';
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
    <Card className="border-gray-200">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-xl">
          <User className="w-5 h-5 text-gray-600" />
          <span>Dados do Participante</span>
        </CardTitle>
      </CardHeader>
      
      <CardContent>
        <div className="grid md:grid-cols-2 gap-6">
          {/* Coluna 1: Dados Pessoais */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
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
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
              Informações Financeiras
            </h3>
            
            <CurrencyInput
              label={
                <span className="flex items-center gap-2">
                  Salário Mensal
                  <InfoTooltip content="Base para cálculo de contribuições e benefícios futuros." />
                </span>
              }
              value={state.salary}
              onValueChange={(value) => handleInputChange('salary', value ?? 0)}
              placeholder="10000"
              min={0}
              step={100}
              disabled={loading}
            />
            
            <CurrencyInput
              label={
                <span className="flex items-center gap-2">
                  Saldo Inicial
                  <InfoTooltip content="Valor já acumulado no plano de previdência." />
                </span>
              }
              value={state.initial_balance}
              onValueChange={(value) => handleInputChange('initial_balance', value ?? 0)}
              placeholder="0"
              min={0}
              step={1000}
              disabled={loading}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ParticipantTab;
