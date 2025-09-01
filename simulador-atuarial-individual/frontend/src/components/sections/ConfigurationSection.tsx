import React from 'react';
import { Icon } from '../../design-system/components/Icon';
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
      icon: <Icon name="user" size="md" color="primary" />,
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
      icon: <Icon name="dollar-sign" size="md" color="success" />,
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
      icon: <Icon name="bar-chart" size="md" className="text-info-600" />,
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