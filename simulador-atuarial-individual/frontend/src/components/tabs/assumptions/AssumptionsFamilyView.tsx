import type { SimulatorState } from '../../../types';
import FamilyCompositionCard from '../../cards/FamilyCompositionCard';

interface AssumptionsFamilyViewProps {
  state: SimulatorState;
  onStateChange: (updates: Partial<SimulatorState>) => void;
}

const AssumptionsFamilyView: React.FC<AssumptionsFamilyViewProps> = ({
  state,
  onStateChange
}) => {
  return (
    <div className="space-y-6">
      <FamilyCompositionCard
        state={state}
        onStateChange={onStateChange}
      />
    </div>
  );
};

export default AssumptionsFamilyView;
