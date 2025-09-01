import React from 'react';
import { Icon } from '../../design-system/components/Icon';
import type { SimulatorState } from '../../types';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardContent,
  Input,
  Select,
  Tooltip,
  Button
} from '../../design-system/components';
import { useFormHandler } from '../../hooks';
import { parseIntegerValue, parseNumericValue } from '../../utils';

interface ParticipantCardProps {
  state: SimulatorState;
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const ParticipantCard: React.FC<ParticipantCardProps> = ({ 
  state, 
  onStateChange, 
  loading 
}) => {
  const { handleInputChange } = useFormHandler({ onStateChange });

  return (
    <Card variant="default" padding="md">
      <CardHeader withBorder>
        <CardTitle className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <Icon name="user" size="md" color="primary" />
          </div>
          Dados do Participante
        </CardTitle>
      </CardHeader>
      
      <CardContent className="pt-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Benefício Alvo */}
          <div className="col-span-2 space-y-1.5">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-semibold text-gray-700">Meta de Aposentadoria</span>
              <Tooltip content="Defina se deseja especificar um valor fixo em reais ou uma taxa de reposição baseada no salário atual">
                <Icon name="help-circle" size="sm" className="text-gray-400 hover:text-gray-600 cursor-help" />
              </Tooltip>
            </div>
            <div className="flex rounded-lg border border-gray-200 overflow-hidden">
              <Button
                variant={state.benefit_target_mode === 'VALUE' ? 'primary' : 'ghost'}
                size="sm"
                className="flex-1 rounded-none border-0"
                onClick={() => handleInputChange('benefit_target_mode', 'VALUE')}
                disabled={loading}
              >
                Valor (R$)
              </Button>
              <Button
                variant={state.benefit_target_mode === 'REPLACEMENT_RATE' ? 'primary' : 'ghost'}
                size="sm"
                className="flex-1 rounded-none border-0 border-l border-gray-200"
                onClick={() => handleInputChange('benefit_target_mode', 'REPLACEMENT_RATE')}
                disabled={loading}
              >
                Taxa de Reposição (%)
              </Button>
            </div>
            
            {state.benefit_target_mode === 'VALUE' ? (
              <Input
                type="number"
                min={0}
                step={100}
                value={state.target_benefit || ''}
                onChange={(e) => handleInputChange('target_benefit', parseNumericValue(e.target.value))}
                disabled={loading}
                placeholder="Ex: 5000"
                leftIcon={<Icon name="dollar-sign" size="sm" color="muted" />}
                helperText="Valor mensal desejado do benefício"
              />
            ) : (
              <Input
                type="number"
                min={0}
                max={200}
                step={5}
                value={state.target_replacement_rate || ''}
                onChange={(e) => handleInputChange('target_replacement_rate', parseNumericValue(e.target.value))}
                disabled={loading}
                placeholder="Ex: 80"
                rightIcon={<span className="text-gray-500 text-sm font-medium">%</span>}
                helperText="Percentual do salário atual que deseja receber"
              />
            )}
          </div>
          {/* Idade */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-gray-700">Idade Atual</span>
              <Tooltip content="Idade do participante em anos completos">
                <Icon name="help-circle" size="sm" className="text-gray-400 hover:text-gray-600 cursor-help" />
              </Tooltip>
            </div>
            <Input
              type="number"
              min={18}
              max={70}
              value={state.age}
              onChange={(e) => handleInputChange('age', parseIntegerValue(e.target.value))}
              disabled={loading}
              placeholder="Ex: 35"
            />
          </div>

        {/* Gênero */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700">Gênero</span>
            <Tooltip content="Utilizado para seleção da tábua de mortalidade apropriada">
              <Icon name="help-circle" size="sm" className="text-gray-400 hover:text-gray-600 cursor-help" />
            </Tooltip>
          </div>
          <Select
            value={state.gender}
            onChange={(e) => handleInputChange('gender', e.target.value as 'M' | 'F')}
            disabled={loading}
            options={[
              { value: 'M', label: 'Masculino' },
              { value: 'F', label: 'Feminino' }
            ]}
          />
        </div>

        {/* Salário Atual */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700">Salário Atual</span>
            <Tooltip content="Salário mensal atual em reais">
              <Icon name="help-circle" size="sm" className="text-gray-400 hover:text-gray-600 cursor-help" />
            </Tooltip>
          </div>
          <Input
            type="number"
            min={0}
            step={100}
            value={state.salary}
            onChange={(e) => handleInputChange('salary', parseNumericValue(e.target.value))}
            disabled={loading}
            placeholder="Ex: 8000"
            leftIcon={<Icon name="dollar-sign" size="sm" color="muted" />}
          />
        </div>

        {/* Saldo Inicial */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700">Saldo Inicial</span>
            <Tooltip content="Reservas acumuladas até o momento">
              <Icon name="help-circle" size="sm" className="text-gray-400 hover:text-gray-600 cursor-help" />
            </Tooltip>
          </div>
          <Input
            type="number"
            min={0}
            step={1000}
            value={state.initial_balance}
            onChange={(e) => handleInputChange('initial_balance', parseNumericValue(e.target.value))}
            disabled={loading}
            placeholder="Ex: 50000"
            leftIcon={<Icon name="dollar-sign" size="sm" color="muted" />}
          />
        </div>

        {/* Idade de Aposentadoria */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700">Idade de Aposentadoria</span>
            <Tooltip content="Idade planejada para aposentadoria">
              <Icon name="help-circle" size="sm" className="text-gray-400 hover:text-gray-600 cursor-help" />
            </Tooltip>
          </div>
          <Input
            type="number"
            min={50}
            max={75}
            value={state.retirement_age}
            onChange={(e) => handleInputChange('retirement_age', parseIntegerValue(e.target.value))}
            disabled={loading}
            placeholder="Ex: 65"
          />
        </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ParticipantCard;