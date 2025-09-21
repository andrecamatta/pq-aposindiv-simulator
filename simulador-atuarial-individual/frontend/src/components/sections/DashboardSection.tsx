import React from 'react';
import type { SimulatorState, SimulatorResults, MortalityTable } from '../../types';
import ParticipantCard from '../cards/ParticipantCard';
import FinancialAssumptionsCard from '../cards/FinancialAssumptionsCard';
import ActuarialBasisCard from '../cards/ActuarialBasisCard';
import ResultsCard from '../cards/ResultsCard';

interface DashboardSectionProps {
  state: SimulatorState;
  results: SimulatorResults | null;
  mortalityTables: MortalityTable[];
  onStateChange: (updates: Partial<SimulatorState>) => void;
  loading: boolean;
}

const DashboardSection: React.FC<DashboardSectionProps> = ({
  state,
  results,
  mortalityTables,
  onStateChange,
  loading
}) => {
  return (
    <div className="min-h-full bg-gray-50">
      {/* Hero Section */}
      <div className="bg-white border-b border-gray-200 px-6 py-8">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            PrevLab
          </h1>
          <p className="text-gray-600 text-lg">
            Configure os parâmetros e visualize os resultados em tempo real
          </p>
        </div>
      </div>

      {/* Cards Grid */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Top Row: Participant + Results */}
          <div className="lg:col-span-4">
            <ParticipantCard
              state={state}
              onStateChange={onStateChange}
              loading={loading}
            />
          </div>
          
          <div className="lg:col-span-8">
            <ResultsCard
              results={results}
              loading={loading}
            />
          </div>

          {/* Middle Row: Financial Assumptions (Full Width) */}
          <div className="lg:col-span-12">
            <FinancialAssumptionsCard
              state={state}
              onStateChange={onStateChange}
              loading={loading}
            />
          </div>

          {/* Bottom Row: Actuarial Basis */}
          <div className="lg:col-span-6">
            <ActuarialBasisCard
              state={state}
              mortalityTables={mortalityTables}
              onStateChange={onStateChange}
              loading={loading}
            />
          </div>

          {/* Future: Charts Card */}
          <div className="lg:col-span-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 h-full">
              <div className="flex items-center justify-center h-full text-gray-400">
                <div className="text-center">
                  <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
                      <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-600 mb-2">Gráficos</h3>
                  <p className="text-sm">Visualizações em desenvolvimento</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardSection;