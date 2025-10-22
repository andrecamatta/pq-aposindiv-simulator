import { useState } from 'react';
import type { SimulatorState } from '../../types';
import AssumptionsSubNavigation, { type AssumptionsSubView } from './AssumptionsSubNavigation';
import AssumptionsFinancialView from './assumptions/AssumptionsFinancialView';
import AssumptionsFamilyView from './assumptions/AssumptionsFamilyView';

interface AssumptionsTabProps {
  state: SimulatorState;
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const AssumptionsTab: React.FC<AssumptionsTabProps> = ({
  state,
  onStateChange,
  loading
}) => {
  const [activeView, setActiveView] = useState<AssumptionsSubView>('financial');

  return (
    <div className="space-y-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Premissas
        </h1>
        <p className="text-gray-600">
          Configure as premissas atuariais, financeiras e familiares para a simulação.
        </p>
      </div>

      <AssumptionsSubNavigation
        activeView={activeView}
        onViewChange={setActiveView}
      />

      {activeView === 'financial' && (
        <AssumptionsFinancialView
          state={state}
          onStateChange={onStateChange}
          loading={loading}
        />
      )}

      {activeView === 'family' && (
        <AssumptionsFamilyView
          state={state}
          onStateChange={onStateChange}
        />
      )}
    </div>
  );
};

export default AssumptionsTab;
