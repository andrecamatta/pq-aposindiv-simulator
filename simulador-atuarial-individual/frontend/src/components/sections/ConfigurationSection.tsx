import React from 'react';
import { User, DollarSign, BarChart3 } from 'lucide-react';
import type { SimulatorState, MortalityTable } from '../../types';
import { Accordion } from '../../design-system/components';
import ParticipantCard from '../cards/ParticipantCard';
import FinancialAssumptionsCard from '../cards/FinancialAssumptionsCard';
import ActuarialBasisCard from '../cards/ActuarialBasisCard';

interface ConfigurationSectionProps {
  state: SimulatorState;
  mortalityTables: MortalityTable[];
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
  defaultExpanded?: string;
}

const ConfigurationSection: React.FC<ConfigurationSectionProps> = ({
  state,
  mortalityTables,
  onStateChange,
  loading,
  defaultExpanded = 'participant'
}) => {
  const accordionItems = [
    {
      id: 'participant',
      title: 'Dados do Participante',
      subtitle: 'Informações básicas e perfil',
      icon: <User className="w-5 h-5 text-primary-600" />,
      content: (
        <ParticipantCard
          state={state}
          onStateChange={onStateChange}
          loading={loading}
        />
      ),
    },
    {
      id: 'financial',
      title: 'Premissas Financeiras',
      subtitle: 'Taxas e valores monetários',
      icon: <DollarSign className="w-5 h-5 text-success-600" />,
      content: (
        <FinancialAssumptionsCard
          state={state}
          onStateChange={onStateChange}
          loading={loading}
        />
      ),
    },
    {
      id: 'actuarial',
      title: 'Base Atuarial',
      subtitle: 'Métodos e tábuas de cálculo',
      icon: <BarChart3 className="w-5 h-5 text-info-600" />,
      content: (
        <ActuarialBasisCard
          state={state}
          mortalityTables={mortalityTables}
          onStateChange={onStateChange}
          loading={loading}
        />
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="text-center pb-2">
        <h2 className="text-lg font-bold text-slate-800 mb-1">Configuração</h2>
        <p className="text-sm text-slate-500">Configure os parâmetros da simulação</p>
      </div>
      
      <Accordion
        items={accordionItems}
        defaultExpanded={defaultExpanded}
        allowMultiple={false}
      />
    </div>
  );
};

export default ConfigurationSection;